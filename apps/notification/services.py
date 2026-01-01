from django.contrib.contenttypes.models import ContentType

from .models import Notification
from .websocket_service import NotificationWebSocketService


def create_notification(
    *, recipient, actor=None, notification_type, title, message="", related_object=None
):
    content_type = None
    object_id = None

    if related_object:
        content_type = ContentType.objects.get_for_model(related_object.__class__)
        object_id = related_object.id

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        message=message,
        content_type=content_type,
        object_id=object_id,
    )

    # Send real-time notification
    NotificationWebSocketService.send_notification(notification)

    return notification
