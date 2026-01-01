from django.db import models

from apps.base.models import BaseModel
from apps.superadmin.models import Users

# Create your models here.


class Conversation(BaseModel):
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


class Message(BaseModel):
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
        return (
            f"Message from {self.sender.email} in {self.conversation.name or 'Unnamed'}"
        )


class MessageStatus(BaseModel):
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
        unique_together = ("message", "user")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.email} - {self.status}"


class MessageReaction(BaseModel):
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
        unique_together = ("message", "user", "emoji")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} reacted {self.emoji} to message"
