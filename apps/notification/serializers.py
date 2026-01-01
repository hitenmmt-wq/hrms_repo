from rest_framework import serializers

from apps.notification.models import Notification, NotificationType
from apps.superadmin.models import Users


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())
    recipient = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "recipient",
            "title",
            "message",
            "actor",
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
