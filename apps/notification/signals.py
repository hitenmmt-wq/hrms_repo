from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.chat.models import Message
from apps.notification.models import NotificationType
from apps.notification.services import create_notification


@receiver(post_save, sender=Message)
def notify_on_message(sender, instance, created, **kwargs):
    if not created:
        return
    notification_type = NotificationType.objects.get(code="chat_message")
    conversation = instance.conversation
    for participant in conversation.participants.exclude(id=instance.sender.id):
        create_notification(
            recipient=participant,
            actor=instance.sender,
            notification_type=notification_type,
            title=f"New message in {conversation.name or 'chat'}",
            message=instance.text[:100] if instance.text else "Media message",
            related_object=instance,
        )
