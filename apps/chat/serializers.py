"""
Chat serializers for real-time messaging data validation and transformation.

Handles serialization for conversations, messages, reactions, and message status
for the HRMS chat system with support for media attachments and reply functionality.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import serializers

from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for chat participant information."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")


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

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "text",
            "media",
            "media_url",
            "msg_type",
            "reply_to",
            "reply_to_id",
            "reactions",
            "reaction_counts",
            "created_at",
        )
        read_only_fields = ("sender", "created_at")

    def get_media_url(self, obj):
        """Generate absolute URL for media attachments."""
        request = self.context.get("request")
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        if obj.media:
            return obj.media.url
        return None

    def get_reply_to(self, obj):
        """Get reply message details for threaded conversations."""
        if obj.reply_to:
            return {
                "id": obj.reply_to.id,
                "text": obj.reply_to.text,
                "sender": UserSerializer(obj.reply_to.sender).data,
            }
        return None

    def get_reaction_counts(self, obj):
        """Get aggregated reaction counts by emoji type."""
        return obj.reactions.values("emoji").annotate(count=Count("emoji"))

    def validate(self, data):
        """Ensure message has either text content or media attachment."""
        if not data.get("text") and not data.get("media"):
            raise serializers.ValidationError("Either text or media must be provided")
        return data


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new conversations with participant selection."""

    participants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True
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

    def get_participants(self, obj):
        """Return participants excluding the current user."""
        request = self.context.get("request")
        if request and request.user:
            other_participants = obj.participants.exclude(id=request.user.id)
            return UserSerializer(other_participants, many=True).data
        return UserSerializer(obj.participants.all(), many=True).data


class MessageStatusSerializer(serializers.ModelSerializer):
    """Serializer for message delivery and read status tracking."""

    class Meta:
        model = MessageStatus
        fields = ("id", "message", "user", "status", "updated_at")
