from django.utils import timezone

from apps.base import constants
from apps.employee.models import LeaveBalance


def update_leave_balance(employee, leave_type=None, status=None, count=0):
    print("update_leave_balance this fucntion called.....")
    today = timezone.now()
    year = today.year

    leave_balance = LeaveBalance.objects.filter(employee=employee, year=year).first()

    if not leave_balance:
        return None

    if status == constants.REJECTED:
        return

    elif status == constants.APPROVED:
        if leave_type == constants.PRIVILEGE_LEAVE:
            leave_balance.used_pl += count
        elif leave_type == constants.SICK_LEAVE:
            leave_balance.used_sl += count
        elif leave_type == constants.OTHER_LEAVE:
            leave_balance.used_lop += count
    else:
        return

    leave_balance.save()
    print(f"==>> leave_balance: {leave_balance.used_pl}")
    return leave_balance
