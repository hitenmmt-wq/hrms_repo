from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.chat.models import Message
from apps.notification.services import create_notification

# from notification.constants import NotificationType


@receiver(post_save, sender=Message)
def notify_on_message(sender, instance, created, **kwargs):
    if not created:
        return

    create_notification(
        recipient=instance.receiver,
        actor=instance.sender,
        notification_type=instance.notification_type,
        title="New Message",
        message=instance.text[:100],
        related_object=instance,
    )
