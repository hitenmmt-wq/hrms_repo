from celery import shared_task
from django.contrib.contenttypes.models import ContentType

from apps.base import constants
from apps.chat.connection_tracker import ChatConnectionTracker
from apps.chat.models import Message
from apps.notification.models import Notification, NotificationType
from apps.notification.websocket_service import NotificationWebSocketService


@shared_task
def create_chat_notification(message_id):
    """Create chat notification asynchronously to avoid WebSocket context issues."""

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return

    try:
        notification_type = NotificationType.objects.get(code=constants.CHAT_NOTIFY)
    except NotificationType.DoesNotExist:
        notification_type = NotificationType.objects.create(
            code=constants.CHAT_NOTIFY, name="Chat Notification"
        )

    conversation = message.conversation
    participants = conversation.participants.exclude(id=message.sender.id)
    for participant in participants:

        worker_tracker = ChatConnectionTracker()

        if not worker_tracker.redis_client:
            print(
                f"❌ Redis unavailable - creating notification for user {participant.id}"
            )
            _create_notification_without_websocket(
                recipient=participant,
                actor=message.sender,
                notification_type=notification_type,
                title=f"New message from {message.sender.first_name} {message.sender.last_name}",
                message=message.text[:100] if message.text else "Media message",
                related_object=message,
            )
            continue

        # Check if user is connected to this conversation
        is_connected = worker_tracker.is_connected(participant.id, conversation.id)
        print(
            f"🔗 User {participant.email} connected to conversation {conversation.id}: {is_connected}"
        )

        # Debug: Show all user connections
        user_connections = worker_tracker.get_user_connections(participant.id)
        print(f"==>> user_connections: {user_connections}")

        # Only create notification if user is NOT connected to this conversation
        if not is_connected:
            _create_notification_without_websocket(
                recipient=participant,
                actor=message.sender,
                notification_type=notification_type,
                title=f"New message from {message.sender.first_name} {message.sender.last_name}",
                message=message.text[:100] if message.text else "Media message",
                related_object=message,
            )
        else:
            print(f"⏭️ Skipping notification for connected user {participant.email}")

    print(f"🏁 CHAT NOTIFICATION TASK COMPLETED for message_id: {message_id}")


def _create_notification_without_websocket(
    *, recipient, actor=None, notification_type, title, message="", related_object=None
):
    """Create notification without triggering WebSocket from async context."""

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

    # Send WebSocket notification in separate task to avoid async context issues
    send_notification_websocket.delay(notification.id)
    return notification


@shared_task
def send_notification_websocket(notification_id):
    """Send notification via WebSocket in separate task."""
    try:
        notification = Notification.objects.get(id=notification_id)
        NotificationWebSocketService.send_notification(notification)
    except Notification.DoesNotExist:
        pass
