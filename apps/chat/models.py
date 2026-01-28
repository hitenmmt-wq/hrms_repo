"""
Chat models for real-time messaging and communication.

Handles conversations, messages, message status tracking, and reactions
for the HRMS internal communication system.
"""

from django.db import models
from django.db.models import Q

from apps.base.models import BaseModel
from apps.superadmin.models import Users


class Conversation(BaseModel):
    """Chat conversations supporting private and group messaging."""

    CONVERSATION_TYPES = (
        ("private", "private"),
        ("group", "group"),
    )
    type = models.CharField(max_length=20, choices=CONVERSATION_TYPES)
    name = models.CharField(max_length=255, null=True, blank=True)
    participants = models.ManyToManyField(Users, related_name="conversations")

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name or 'Unnamed'} - {self.type}"

    def get_unread_count(self, user):
        """Get unread message count for a specific user."""
        return (
            MessageStatus.objects.filter(
                message__conversation=self,
                message__is_deleted=False,
                user=user,
                is_deleted=False,
                status__in=["sent", "delivered"],
            )
            .exclude(message__sender=user)
            .count()
        )

    def get_last_read_message_by_user(self, user, sender):
        print(f"==>> sender: {sender}")
        print(f"==>> user: {user}")
        """Get the last message sent by sender that was read by user."""
        last_read_status = (
            MessageStatus.objects.filter(
                message__conversation=self,
                message__is_deleted=False,
                message__sender=sender,
                user=user,
                is_deleted=False,
                status="read",
            )
            .select_related("message")
            .order_by("-message__created_at")
            .first()
        )
        print(f"==>> last_read_status: {last_read_status}")

        return last_read_status.message.id if last_read_status else None

    def get_read_receipts_for_sender(self, sender):
        """Get last read message ID for each participant (messages sent by sender, read by others)."""
        participants = self.participants.exclude(id=sender.id)
        read_receipts = {}

        for participant in participants:
            # Get last message sent by sender that was read by participant
            last_read_msg_id = self.get_last_read_message_by_user(participant, sender)
            read_receipts[participant.id] = {
                "user_id": participant.id,
                "user_name": f"{participant.first_name} {participant.last_name}",
                "last_read_message_id": last_read_msg_id,
            }

        return read_receipts


class Message(BaseModel):
    """Individual messages with text, media, and reply support."""

    MSG_TYPE_CHOICES = (
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("audio", "Audio"),
        ("video", "Video"),
    )

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="sent_messages"
    )
    text = models.TextField(null=True, blank=True)
    media = models.FileField(upload_to="chat_media/", null=True, blank=True)
    msg_type = models.CharField(max_length=20, choices=MSG_TYPE_CHOICES, default="text")
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["msg_type"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message({self.id}) from {self.sender.email} in {self.conversation.name or 'Unnamed'}"

    def get_status_for_user(self, user):
        """
        Returns message status from POV of a user
        """
        if self.sender_id == user:
            statuses = self.statuses.values_list("status", flat=True)

            if not statuses:
                return "sent"

            if all(s == "read" for s in statuses):
                return "read"

            if any(s in ["delivered", "read"] for s in statuses):
                return "delivered"

            return "sent"

        status_obj = self.statuses.filter(user=user).first()
        return status_obj.status if status_obj else "sent"


class MessageStatus(BaseModel):
    """Message delivery and read status tracking per user."""

    STATUS_CHOICES = (
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
        ("failed", "Failed"),
    )

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="statuses"
    )
    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="message_statuses"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                condition=Q(is_deleted=False),
                name="unique_active_message_per_user",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.email} - {self.status} - conv: {self.message.conversation.id}"
        )


class MessageReaction(BaseModel):
    """Emoji reactions to messages for enhanced communication."""

    REACTION_CHOICES = (
        ("👍", "Thumbs Up"),
        ("❤️", "Heart"),
        ("😂", "Laugh"),
        ("😮", "Wow"),
        ("😢", "Sad"),
        ("😡", "Angry"),
    )

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="message_reactions"
    )
    emoji = models.CharField(max_length=10, choices=REACTION_CHOICES)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user", "emoji"],
                condition=Q(is_deleted=False),
                name="unique_active_emoji_per_message",
            )
        ]

    def __str__(self):
        return f"{self.user.email} reacted {self.emoji} to message"
