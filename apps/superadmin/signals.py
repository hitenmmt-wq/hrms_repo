from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone

from apps.superadmin.models import Users


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
