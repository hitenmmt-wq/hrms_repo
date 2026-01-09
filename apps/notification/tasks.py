from celery import shared_task

from apps.base import constants
from apps.chat.connection_tracker import chat_tracker
from apps.chat.models import Message
from apps.notification.models import NotificationType
from apps.notification.services import create_notification


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
    for participant in conversation.participants.exclude(id=message.sender.id):
        # Only create notification if user is NOT connected to this conversation
        if not chat_tracker.is_connected(participant.id, conversation.id):
            create_notification(
                recipient=participant,
                actor=message.sender,
                notification_type=notification_type,
                title=f"New message in {conversation.name or 'chat'}",
                message=message.text[:100] if message.text else "Media message",
                related_object=message,
            )
