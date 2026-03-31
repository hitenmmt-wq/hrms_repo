"""
Chat serializers for real-time messaging data validation and transformation.

Handles serialization for conversations, messages, reactions, and message status
for the HRMS chat system with support for media attachments and reply functionality.
"""

# from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers

from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus
from apps.superadmin.models import Users

# User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for chat participant information."""

    profile = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("id", "email", "first_name", "last_name", "profile")

    def get_profile(self, obj):
        request = self.context.get("request")
        if obj.profile:
            if request:
                return request.build_absolute_uri(obj.profile.url)
            return obj.profile.url
        return None


class MessageReactionSerializer(serializers.ModelSerializer):
    """Serializer for message emoji reactions with user details."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ("id", "user", "emoji", "created_at")
        read_only_fields = ("user", "created_at")


class MessageSerializer(serializers.ModelSerializer):
    """Comprehensive message serializer with media, reactions, and reply support."""

    sender = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reply_to_id = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        source="reply_to",
        write_only=True,
        required=False,
        allow_null=True,
    )
    reply_to = serializers.SerializerMethodField()
    reaction_counts = serializers.SerializerMethodField()
    read_by = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "text",
            "encrypted_text",
            "is_encrypted",
            "nonce",
            "is_edited",
            "media",
            "media_url",
            "msg_type",
            "reply_to",
            "reply_to_id",
            "reactions",
            "reaction_counts",
            "read_by",
            "created_at",
        )
        read_only_fields = (
            "sender",
            "created_at",
            "encrypted_text",
            "is_encrypted",
            "nonce",
        )

    def get_media_url(self, obj):
        """Generate absolute URL for media attachments."""
        request = self.context.get("request")
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        if obj.media:
            return obj.media.url
        return None

    def get_reply_to(self, obj):
        """Get reply message details for threaded conversations (supports encrypted messages)."""
        if obj.reply_to:
            return {
                "id": obj.reply_to.id,
                "text": obj.reply_to.text,
                "encrypted_text": obj.reply_to.encrypted_text,
                "nonce": obj.reply_to.nonce,  # Critical for decrypting replied message
                "is_encrypted": obj.reply_to.is_encrypted,
                "msg_type": obj.reply_to.msg_type,
                "sender": UserSerializer(
                    obj.reply_to.sender, context=self.context
                ).data,
                "created_at": obj.reply_to.created_at.isoformat(),
            }
        return None

    def get_reaction_counts(self, obj):
        """Get aggregated reaction counts by emoji type."""
        return obj.reactions.values("emoji").annotate(count=Count("emoji"))

    def get_read_by(self, obj):
        """Get list of users who have read this message."""
        read_statuses = MessageStatus.objects.filter(
            message=obj, is_deleted=False, status="read"
        ).select_related("user")

        return [
            {
                "user_id": status.user.id,
                "user_name": f"{status.user.first_name} {status.user.last_name}",
                "read_at": status.updated_at,
            }
            for status in read_statuses
        ]

    def validate(self, data):
        """Ensure message has either text content, encrypted_text, or media attachment."""
        has_content = (
            data.get("text") or data.get("encrypted_text") or data.get("media")
        )
        if not has_content:
            raise serializers.ValidationError(
                "Either text, encrypted_text, or media must be provided"
            )
        return data


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new conversations with participant selection."""

    participants = serializers.PrimaryKeyRelatedField(
        queryset=Users.objects.all(), many=True
    )
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "type",
            "name",
            "participants",
            "created_at",
            "messages",
        )


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for displaying conversations with participants and messages."""

    participants = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    read_receipts = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "type",
            "name",
            "profile",
            "participants",
            "created_at",
            "unread_count",
            "last_message",
            "read_receipts",
        )

    def get_profile(self, obj):
        """Get profile image URL for group conversations."""
        request = self.context.get("request")
        if obj.profile:
            if request:
                return request.build_absolute_uri(obj.profile.url)
            return obj.profile.url
        return None

    def get_participants(self, obj):
        """Return participants excluding the current user."""
        request = self.context.get("request")
        if request and request.user:
            other_participants = obj.participants.exclude(id=request.user.id)
            return UserSerializer(
                other_participants, many=True, context=self.context
            ).data
        return UserSerializer(
            obj.participants.all(), many=True, context=self.context
        ).data

    def get_unread_count(self, obj):
        """Calculate unread messages for the current user in the conversation."""
        request = self.context.get("request")
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0

    def get_last_message(self, obj):
        """Get the last message in the conversation."""
        last_msg = obj.messages.filter(is_deleted=False).first()
        if last_msg:
            return {
                "id": last_msg.id,
                "text": last_msg.text,
                "sender_id": last_msg.sender.id,
                "sender_name": f"{last_msg.sender.first_name} {last_msg.sender.last_name}",
                "created_at": last_msg.created_at,
                "msg_type": last_msg.msg_type,
            }
        return None

    def get_read_receipts(self, obj):
        """Get last read message for each participant (for sender to see)."""
        request = self.context.get("request")
        if request and request.user:
            return obj.get_read_receipts_for_sender(request.user)
        return {}


class MessageStatusSerializer(serializers.ModelSerializer):
    """Serializer for message delivery and read status tracking."""

    class Meta:
        model = MessageStatus
        fields = ("id", "message", "user", "status", "updated_at")
