from rest_framework import serializers
from .models import Conversation, Message, MessageStatus
from django.contrib.auth import get_user_model


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ('id', 'conversation', 'sender', 'text', 'media', 'media_url', 'msg_type', 'reply_to', 'created_at')
        read_only_fields = ('sender', 'created_at')


    def get_media_url(self, obj):
        request = self.context.get('request')
        if obj.media and request:
            return request.build_absolute_uri(obj.media.url)
        if obj.media:
            return obj.media.url
        return None


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ('id', 'type', 'name', 'participants', 'admins', 'created_at', 'messages')


class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageStatus
        fields = ('id', 'message', 'user', 'status', 'updated_at')