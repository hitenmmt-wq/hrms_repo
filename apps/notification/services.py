from django.contrib.contenttypes.models import ContentType

from apps.base import constants

from .models import Notification
from .websocket_service import NotificationWebSocketService


def get_notification_url(notification_type, recipient):
    code = getattr(notification_type, "code", None)
    if recipient.role == constants.ADMIN_USER:
        return constants.NOTIFICATION_URL_MAP_ADMIN.get(code, "/")
    return constants.NOTIFICATION_URL_MAP.get(code, "/")


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
        url=get_notification_url(notification_type, recipient),
        content_type=content_type,
        object_id=object_id,
    )

    # Send real-time notification
    NotificationWebSocketService.send_notification(notification)

    return notification
