from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.employee.models import LeaveBalance
from apps.notification.models import NotificationType
from apps.notification.services import create_notification
from apps.superadmin.models import CommonData


@receiver(post_save, sender=LeaveBalance)
def leave_balance_post_save(sender, instance, **kwargs):
    print("this signal called.....leave_balance_post_save.........")
    if instance.pk:
        return

    common_data = CommonData.objects.first()

    instance.pl = common_data.pl_leaves if common_data else 12
    instance.sl = common_data.sl_leaves if common_data else 4
    instance.lop = common_data.lop_leaves if common_data else 0


@receiver(post_save, sender=EmployeeAttendance)
def notify_on_attendance(sender, instance, created, **kwargs):
    print("this signal called.....notify_on_attendance.........")
    if (
        instance.check_in
        and not instance.check_out
        and instance.work_hours == 0
        and instance.break_hours == 0
    ):
        notification_type = NotificationType.objects.filter(
            code=constants.ATTENDANCE_REMINDER
        ).first()
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Attendance Alert",
            message="Let's begin on a positive note.",
            related_object=instance,
        )

    if instance.check_in and instance.check_out and instance.work_hours >= 0:
        notification_type = NotificationType.objects.filter(
            code=constants.ATTENDANCE_REMINDER
        ).first()
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Attendance Alert",
            message="Wrapped up for the day, see you soon.",
            related_object=instance,
        )

    if instance.check_out:
        if instance.status == constants.PENDING:
            notification_type = NotificationType.objects.filter(
                code=constants.PENDING
            ).first()
            create_notification(
                recipient=instance.employee,
                notification_type=notification_type,
                title="Working Hours",
                message="Your attendance request is pending.",
                related_object=instance,
            )

        if instance.status == constants.PRESENT:
            notification_type = NotificationType.objects.filter(
                code=constants.APPROVED
            ).first()
            create_notification(
                recipient=instance.employee,
                notification_type=notification_type,
                title="Working Hours",
                message="Your attendance has been completed.",
                related_object=instance,
            )

        if instance.status == constants.REJECTED:
            notification_type = NotificationType.objects.filter(
                code=constants.ATTENDANCE_REJECTED
            ).first()
            create_notification(
                recipient=instance.employee,
                notification_type=notification_type,
                title="Working Hours",
                message="Your attendance has been rejected.",
                related_object=instance,
            )

        if instance.status == constants.INCOMPLETE_HOURS:
            notification_type = NotificationType.objects.filter(
                code=constants.ATTENDANCE_REMINDER
            ).first()
            create_notification(
                recipient=instance.employee,
                notification_type=notification_type,
                title="Working Hours",
                message="Your work hours are incomplete today.",
                related_object=instance,
            )
