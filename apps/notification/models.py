"""
Notification models for system-wide alerts and messaging.

Handles notification types, user notifications with generic content linking,
and read status tracking for the HRMS notification system.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.base.models import BaseModel
from apps.superadmin.models import Users


class DeviceToken(models.Model):
    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="device_tokens"
    )
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email


class NotificationType(BaseModel):
    """Notification categories and types for system alerts."""

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Notification(BaseModel):
    """User notifications with generic content linking and read tracking."""

    recipient = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="notifications"
    )

    actor = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actor_notifications",
    )

    notification_type = models.ForeignKey(
        NotificationType, on_delete=models.PROTECT, related_name="notification_types"
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["notification_type"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} → {self.recipient}"
