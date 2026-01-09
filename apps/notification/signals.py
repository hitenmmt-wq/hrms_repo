from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.chat.models import Message


@receiver(post_save, sender=Message)
def notify_on_message(sender, instance, created, **kwargs):
    if not created:
        return

    # Use Celery task to avoid async context issues
    from celery import current_app

    current_app.send_task(
        "apps.notification.tasks.create_chat_notification", args=[instance.id]
    )
