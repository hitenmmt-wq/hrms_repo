from rest_framework import serializers

from apps.notification.models import Notification, NotificationType


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)
    recipient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "recipient",
            "title",
            "message",
            "actor_name",
            "is_read",
            "created_at",
            "object_id",
        ]


class NotificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationType
        fields = [
            "id",
            "code",
            "name",
        ]
