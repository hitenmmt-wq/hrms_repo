from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.employee.models import LeaveBalance, PaySlip
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
        and created
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
                title="Working Hours Alert",
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
                title="Working Hours Alert",
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
                title="Working Hours Alert",
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
                title="Working Hours Alert",
                message="Your work hours are incomplete today.",
                related_object=instance,
            )


@receiver(post_save, sender=PaySlip)
def notify_on_payslip_generated(sender, instance, created, **kwargs):
    print("this signal called.....notify_on_payslip_generated.........")
    if created:
        notification_type = NotificationType.objects.filter(
            code=constants.PAYSLIP_GENERATED
        ).first()
        create_notification(
            recipient=instance.employee,
            notification_type=notification_type,
            title="Payslip Generated",
            message="Your payslip has been generated.",
            related_object=instance,
        )
        print(f"==>> notification_type: {notification_type}")


# @receiver(post_save, sender=LeaveBalance)
# def update_employee_leave_balance(sender, instance, **kwargs):
#     print("this signal called.....update_employee_leave_balance.........")
#     from dateutil.relativedelta import relativedelta
#     from django.utils import timezone
#     today = timezone.now().date()
#     if instance.pk:
#         return
#     employees = Users.objects.filter(is_active=True).exclude(role="admin")
#     for employee in employees:
#         leave_balance = LeaveBalance.objects.filter(employee=employee).first()
#         if leave_balance:
#             pass
#         else:
#             leave_balance = LeaveBalance.objects.create(employee=employee,year=today.year)
#             joining_date = employee.joining_date
#             probation_end_date = joining_date + relativedelta(months=3)
#             print(f"==>> probation_end_date: {probation_end_date}")
#             leave_balance.pl = 12 - int(probation_end_date.month)
#             if probation_end_date.month <= 3:
#                 leave_balance.sl = 4
#                 leave_balance.lop = 0
#             elif probation_end_date.month <= 6:
#                 leave_balance.sl = 3
#                 leave_balance.lop = 0
#             elif probation_end_date.month <= 9:
#                 leave_balance.sl = 2
#                 leave_balance.lop = 0
#             else:
#                 leave_balance.sl = 1
#                 leave_balance.lop = 0

#             leave_balance.save()
#             print(f"leave updated perfectly, Thank you...")

# @receiver(post_save, sender=Leave)
# def leave_update_to_reporting_manager(employee, leave, **kwargs):
#     from django.utils import timezone
#     today = timezone.now().date()
#     if employee.role != "employee":
#         return
#     reporting_manager = employee.reporting_manager
#     if reporting_manager:
#         receipent = reporting_manager
#         notification_type = NotificationType.objects.filter(
#             code=constants.LEAVE_APPLY
#         ).first()
#         if leave.to_date:
#             message=f"{employee.first_name} {employee.last_name}
#                       has applied for leave from {leave.from_date} to {leave.to_date}.",
#         message=f"{employee.first_name} {employee.last_name} has applied for leave on {leave.from_date}.",
#         create_notification(
#             receipent=receipent,
#             notification_type=notification_type,
#             title="Leave Application",
#             message=message,
#             related_object=leave,
#         )
#     else:
#         return "No reporting manager assigned for this employee."

# @receiver(post_save, sender=EmployeeAttendance)
# def attendance_notify_to_reporting_manager(attendance, **kwargs):
#     employee = attendance.employee
#     reporting_manager = employee.reporting_manager
#     if reporting_manager:
#         receipent = reporting_manager
#         notification_type = NotificationType.objects.filter(
#             code=constants.ATTENDANCE_REMINDER
#         ).first()
#         message=f"{employee.first_name} {employee.last_name} has marked attendance on {attendance.check_in}.",
#         create_notification(
#             receipent=receipent,
#             notification_type=notification_type,
#             title="Attendance Marked",
#             message=message,
#             related_object=attendance,
#         )
#     else:
#         return "No reporting manager assigned for this employee."
