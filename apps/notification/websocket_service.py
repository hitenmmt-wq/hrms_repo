import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notification.models import Notification
from apps.notification.serializers import NotificationSerializer

logger = logging.getLogger(__name__)


class NotificationWebSocketService:
    @staticmethod
    def send_notification(notification):
        """Send new notification via WebSocket"""
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("No channel layer available")
            return

        serializer = NotificationSerializer(notification)
        group_name = f"notifications_{notification.recipient.id}"

        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification_message",
                    "payload": {
                        "type": "new_notification",
                        "notification": serializer.data,
                        "unread_count": Notification.objects.filter(
                            recipient=notification.recipient, is_read=False
                        ).count(),
                    },
                },
            )
            logger.info(f"Sent notification to group: {group_name}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    @staticmethod
    def send_read_update(user_id, notification_id):
        """Send notification read update via WebSocket"""
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("No channel layer available")
            return

        group_name = f"notifications_{user_id}"

        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification_message",
                    "payload": {
                        "type": "notification_read",
                        "notification_id": notification_id,
                        "unread_count": Notification.objects.filter(
                            recipient_id=user_id, is_read=False
                        ).count(),
                    },
                },
            )
            logger.info(f"Sent read update to group: {group_name}")
        except Exception as e:
            logger.error(f"Failed to send read update: {e}")

    @staticmethod
    def send_bulk_update(user_id, update_type="bulk_read"):
        """Send bulk notification update via WebSocket"""
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("No channel layer available")
            return

        group_name = f"notifications_{user_id}"

        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification_message",
                    "payload": {
                        "type": update_type,
                        "unread_count": Notification.objects.filter(
                            recipient_id=user_id, is_read=False
                        ).count(),
                    },
                },
            )
            logger.info(f"Sent bulk update to group: {group_name}")
        except Exception as e:
            logger.error(f"Failed to send bulk update: {e}")
