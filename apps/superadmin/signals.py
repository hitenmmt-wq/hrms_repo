from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.base import constants
from apps.notification.models import NotificationType
from apps.notification.services import create_notification
from apps.superadmin.models import Announcement, Users


@receiver(pre_save, sender=Users)
def assign_employee_id(sender, instance, **kwargs):

    if instance.employee_id:
        return

    year = timezone.now().year
    prefix = f"EMP{year}"

    with transaction.atomic():
        last_user = (
            Users.objects.select_for_update()
            .filter(employee_id__startswith=prefix)
            .order_by("-employee_id")
            .first()
        )

        if last_user and last_user.employee_id:
            last_seq = int(last_user.employee_id[-3:])
            next_seq = last_seq + 1
        else:
            next_seq = 1

        instance.employee_id = f"{prefix}{str(next_seq).zfill(3)}"


@receiver(post_save, sender=Announcement)
def notify_on_announcement(sender, instance, created, **kwargs):
    if not created:
        return
    notification_type = NotificationType.objects.get(code=constants.ANNOUNCEMENT_NOTIFY)
    employees = Users.objects.filter(is_active=True)
    for employee in employees:
        create_notification(
            recipient=employee,
            notification_type=notification_type,
            title=instance.title,
            message=instance.description[:200],
            related_object=instance,
        )
