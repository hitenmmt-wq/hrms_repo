from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.employee.models import LeaveBalance
from apps.superadmin.models import CommonData


@receiver(post_save, sender=LeaveBalance)
def leave_balance_post_save(sender, instance, **kwargs):
    print("this signal called.....leave_balance_post_save.........")
    # if created:
    #     common_data = CommonData.objects.first()
    #     print(f"==>> common_data: {common_data}")
    #     instance.pl = common_data.pl_leaves if common_data else 12
    #     instance.sl = common_data.sl_leaves if common_data else 4
    #     instance.lop = common_data.lop_leaves if common_data else 0
    #     instance.save()
    if instance.pk:
        return

    common_data = CommonData.objects.first()

    instance.pl = common_data.pl_leaves if common_data else 12
    instance.sl = common_data.sl_leaves if common_data else 4
    instance.lop = common_data.lop_leaves if common_data else 0
