from rest_framework import serializers

from .models import AIConversation, AIMessage, AIQueryLog


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for AI messages."""

    class Meta:
        model = AIMessage
        fields = [
            "id",
            "message_type",
            "content",
            "metadata",
            "response_time",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AIConversationSerializer(serializers.ModelSerializer):
    """Serializer for AI conversations."""

    messages = AIMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIConversation
        fields = [
            "id",
            "session_id",
            "title",
            "is_active",
            "context_data",
            "created_at",
            "updated_at",
            "messages",
            "message_count",
            "last_message",
        ]
        read_only_fields = ["id", "session_id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        """Get total message count in conversation."""
        return obj.messages.count()

    def get_last_message(self, obj):
        """Get the last message in conversation."""
        last_message = obj.messages.order_by("-created_at").first()
        if last_message:
            return {
                "content": (
                    last_message.content[:100] + "..."
                    if len(last_message.content) > 100
                    else last_message.content
                ),
                "message_type": last_message.message_type,
                "created_at": last_message.created_at,
            }
        return None


class AIQueryLogSerializer(serializers.ModelSerializer):
    """Serializer for AI query logs."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AIQueryLog
        fields = [
            "id",
            "user_email",
            "user_name",
            "query",
            "intent",
            "data_accessed",
            "response_quality",
            "processing_time",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_user_name(self, obj):
        """Get user's full name."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class QuickQuerySerializer(serializers.Serializer):
    """Serializer for quick AI queries."""

    message = serializers.CharField(max_length=1000)

    def validate_message(self, value):
        """Validate message content."""
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()
