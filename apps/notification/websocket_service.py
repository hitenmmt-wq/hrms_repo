import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notification.models import Notification
from apps.notification.serializers import NotificationSerializer

logger = logging.getLogger(__name__)


class NotificationWebSocketService:
    @staticmethod
    def _get_safe_channel_layer():
        """Get channel layer with Redis availability check"""
        try:
            channel_layer = get_channel_layer()
            return channel_layer
        except Exception:
            return None

    @staticmethod
    def send_notification(notification):
        """Send new notification via WebSocket"""
        if (
            not notification
            or not hasattr(notification, "recipient")
            or not notification.recipient
        ):
            return

        channel_layer = NotificationWebSocketService._get_safe_channel_layer()
        if not channel_layer:
            print("Channel layer not available for WebSocket notification")
            return

        try:
            serializer = NotificationSerializer(notification)
            group_name = f"notifications_{notification.recipient.id}"
            payload = {
                "type": "notification_message",
                "payload": {
                    "type": "new_notification",
                    "notification": serializer.data,
                    "unread_count": Notification.objects.filter(
                        recipient=notification.recipient, is_read=False
                    ).count(),
                },
            }

            print(f"Sending notification to group: {group_name}")
            print(f"Payload: {payload}")

            async_to_sync(channel_layer.group_send)(group_name, payload)
            print("Notification sent successfully via WebSocket")
        except Exception as e:
            print(f"Error sending notification via WebSocket: {e}")
            import traceback

            traceback.print_exc()

    @staticmethod
    def send_read_update(user_id, notification_id):
        """Send notification read update via WebSocket"""
        channel_layer = NotificationWebSocketService._get_safe_channel_layer()
        if not channel_layer:
            return

        try:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
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
        except Exception:
            pass

    @staticmethod
    def send_count_update(user_id, unread_count=None):
        """Send only unread count update via WebSocket"""
        channel_layer = NotificationWebSocketService._get_safe_channel_layer()
        if not channel_layer:
            return

        try:
            if unread_count is None:
                unread_count = Notification.objects.filter(
                    recipient_id=user_id, is_read=False
                ).count()

            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
                {
                    "type": "notification_message",
                    "payload": {
                        "type": "count_update",
                        "unread_count": unread_count,
                    },
                },
            )
        except Exception:
            pass

    @staticmethod
    def send_bulk_update(user_id, update_type="bulk_read"):
        """Send bulk notification update via WebSocket"""
        channel_layer = NotificationWebSocketService._get_safe_channel_layer()
        if not channel_layer:
            return

        try:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
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
        except Exception:
            pass
