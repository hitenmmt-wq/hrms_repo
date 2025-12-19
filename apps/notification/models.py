from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.base.models import BaseModel
from apps.superadmin.models import Users

# Create your models here.


class NotificationType(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Notification(BaseModel):
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
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type} → {self.recipient}"
