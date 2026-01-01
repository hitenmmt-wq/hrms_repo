import calendar
from datetime import date, datetime

from django.utils import timezone

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.employee.models import LeaveBalance
from apps.employee.utils import weekdays_count
from apps.notification.models import NotificationType
from apps.notification.services import create_notification
from apps.superadmin.models import Holiday, Users


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


def general_team_monthly_data():
    # Work pending
    month = datetime.now().month
    year = datetime.now().year
    month_last_day = calendar.monthrange(year, month)[1]
    days = weekdays_count(date(year, month, 1), date(year, month, month_last_day))
    leaves = Holiday.objects.filter(date__month=month, date__year=year).count()
    working_days_of_month = days - leaves
    total_active_employees = Users.objects.filter(
        role=constants.EMPLOYEE_USER, is_active=True
    )
    expected_hours = (working_days_of_month * 8) * total_active_employees.count()
    employees_completion_hours = 0
    for employee in total_active_employees:
        attendance_data = EmployeeAttendance.objects.filter(
            employee=employee, day__month=month, day__year=year
        )
        for attendance in attendance_data:
            employees_completion_hours += attendance.work_hours

    data = {
        "working_days_of_month": working_days_of_month,
        "expected_hours": expected_hours,
        "team_completion_percentage": employees_completion_hours,
    }
    return data


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
