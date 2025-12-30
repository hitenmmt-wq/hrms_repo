from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")


class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ("id", "user", "emoji", "created_at")
        read_only_fields = ("user", "created_at")


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()
    reactions = MessageReactionSerializer(many=True, read_only=True)
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
            "reactions",
            "reaction_counts",
            "created_at",
        )
        read_only_fields = ("sender", "created_at")

    def get_media_url(self, obj):
        request = self.context.get("request")
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        if obj.media:
            return obj.media.url
        return None

    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                "id": obj.reply_to.id,
                "text": obj.reply_to.text,
                "sender": UserSerializer(obj.reply_to.sender).data,
            }
        return None

    def get_reaction_counts(self, obj):
        from django.db.models import Count

        return obj.reactions.values("emoji").annotate(count=Count("emoji"))

    def validate(self, data):
        if not data.get("text") and not data.get("media"):
            raise serializers.ValidationError("Either text or media must be provided")
        return data


class ConversationCreateSerializer(serializers.ModelSerializer):
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
    participants = UserSerializer(many=True, read_only=True)
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


class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageStatus
        fields = ("id", "message", "user", "status", "updated_at")
