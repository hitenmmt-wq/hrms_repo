from django.utils import timezone

from apps.base import constants
from apps.employee.models import LeaveBalance
from apps.notification.models import NotificationType
from apps.notification.services import create_notification


def update_leave_balance(employee, leave_type=None, status=None, count=0):
    print("update_leave_balance this function called.....")
    print(f"==>> leave_type: {leave_type}")
    today = timezone.now()
    year = today.year

    leave_balance = LeaveBalance.objects.filter(employee=employee, year=year).first()

    if not leave_balance:
        return None

    if status == constants.REJECTED:
        return

    elif status == constants.APPROVED:
        if leave_type and leave_type.code == constants.PRIVILEGE_LEAVE:
            leave_balance.used_pl += count
        elif leave_type and leave_type.code == constants.SICK_LEAVE:
            leave_balance.used_sl += count
        elif leave_type and leave_type.code == constants.HALFDAY_LEAVE:
            leave_balance.used_pl += count
        # elif leave_type and leave_type.code == constants.OTHER_LEAVE:
        #     leave_balance.used_lop += count
        else:
            leave_balance.used_lop += count
    else:
        return

    leave_balance.save()
    return leave_balance


def notify_employee_leave_approved(employee, leave):
    if leave.status != constants.APPROVED:
        return
    notification_type = NotificationType.objects.get(code=constants.LEAVE_APPLY)
    create_notification(
        recipient=employee,
        notification_type=notification_type,
        title="Leave Approved",
        message="Your leave has been approved.",
    )


def notify_employee_leave_rejected(employee, leave):
    if leave.status != constants.REJECTED:
        return
    notification_type = NotificationType.objects.get(code=constants.LEAVE_APPLY)
    create_notification(
        recipient=employee,
        notification_type=notification_type,
        title="Leave Rejected",
        message="Your leave has been rejected.",
    )
