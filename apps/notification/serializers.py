"""
Notification serializers for system alert data validation and transformation.

Handles serialization for notifications, notification types, and user alert
management for the HRMS notification system.
"""

from rest_framework import serializers

from apps.notification.models import Notification, NotificationType
from apps.superadmin.models import Users


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications with actor and recipient details."""

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
    """Serializer for notification type configuration and management."""

    class Meta:
        model = NotificationType
        fields = [
            "id",
            "code",
            "name",
        ]
