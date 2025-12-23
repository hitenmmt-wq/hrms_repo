from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.attendance.models import EmployeeAttendance
from apps.employee.models import LeaveBalance
from apps.notification.models import NotificationType
from apps.notification.services import create_notification
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


@receiver(post_save, sender=EmployeeAttendance)
def notify_on_attendance(sender, instance, created, **kwargs):
    print("this signal called.....notify_on_attendance.........")
    print(f"==>> instance.status: {instance.status}")
    if instance.status == "pending":
        notification_type = NotificationType.objects.get(code="pending")
        print(f"==>> notification_type: {notification_type}")
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Attendance Pending",
            message="Your attendance request is pending.",
            related_object=instance,
        )

    if instance.status == "present":
        notification_type = NotificationType.objects.get(code="approved")
        print(f"==>> notification_type: {notification_type}")
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Attendance Completed",
            message="Your attendance has been completed.",
            related_object=instance,
        )

    if instance.status == "rejected":
        notification_type = NotificationType.objects.get(code="attendance_rejected")
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Attendance Rejected",
            message="Your attendance has been rejected.",
            related_object=instance,
        )

    if instance.status == "incomplete_hours":
        notification_type = NotificationType.objects.get(code="attendance_reminder")
        print(f"==>> notification_type: {notification_type}")
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Attendance Reminder",
            message="Your work hours are incomplete today.",
            related_object=instance,
        )
