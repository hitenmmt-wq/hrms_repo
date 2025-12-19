from django.utils import timezone

from apps.employee.models import LeaveBalance


def update_leave_balance(employee, leave_type=None, status=None, count=0):
    print(f"==>> count: {count}")
    print(f"==>> leave_type: {leave_type}")
    print(f"==>> status: {status}")
    print("update_leave_balance this fucntion called.....")
    today = timezone.now()
    year = today.year

    leave_balance = LeaveBalance.objects.filter(employee=employee, year=year).first()

    if not leave_balance:
        return None

    if status == "rejected":
        return
    elif status == "approved":
        if leave_type == "privilege":
            leave_balance.used_pl += count
        elif leave_type == "sick":
            leave_balance.used_sl += count
        elif leave_type == "other":

            leave_balance.used_lop += count
    else:
        return

    leave_balance.save()
    print(f"==>> leave_balance: {leave_balance.used_pl}")
    return leave_balance
