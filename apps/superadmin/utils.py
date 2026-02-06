import calendar
import math
from datetime import date

import pdfplumber
from django.utils import timezone
from docx import Document

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
    # current_month = today.month

    leave_balance = LeaveBalance.objects.filter(employee=employee, year=year).first()

    if not leave_balance:
        return None

    if status == constants.REJECTED:
        return

    elif status == constants.APPROVED:
        if leave_type and leave_type.code == constants.PRIVILEGE_LEAVE:
            pending_pl = get_pending_monthly_pl(leave_balance, today.date())
            apply_pl_usage(leave_balance, pending_pl, count)

        elif leave_type and leave_type.code == constants.SICK_LEAVE:
            pending_sl = get_pending_quarter_sl(leave_balance, today.date())
            if pending_sl >= count:
                leave_balance.used_sl += count
            else:
                if pending_sl > 0:
                    leave_balance.used_sl += pending_sl
                    leave_balance.used_lop += count - pending_sl
                else:
                    leave_balance.used_lop += count
        elif leave_type and leave_type.code == constants.HALFDAY_LEAVE:
            pending_pl = get_pending_monthly_pl(leave_balance, today.date())
            apply_pl_usage(leave_balance, pending_pl, count)
        else:
            # Other leave types go to LOP
            leave_balance.used_lop += count
    else:
        return

    leave_balance.save()
    return leave_balance


def general_team_monthly_data():
    # Work pending
    month = timezone.now().month
    year = timezone.now().year
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


def extract_pdf_content(file):
    text_blocks = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_blocks.append(text)

    print("done with extraction")
    data = "\n\n".join(text_blocks)
    return data


def extract_docx_content(file):
    doc = Document(file)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    print("done with extraction")
    return "\n".join(paragraphs)


def extract_text_content(file):
    print(f"==>> file: {file}")
    return file.read().decode("utf-8")


def extract_file_data(file):
    file.seek(0)
    print(f"==>> handbook_file: {file}")
    file_type = file.name.split(".")[-1].lower()
    print(f"==>> file_type: {file_type}")

    ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"]

    if not file.name.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        return "Unsupported file format"

    if file_type == "pdf":
        data = extract_pdf_content(file)
        return data
    elif file_type == "docx":
        data = extract_docx_content(file)
        return data
    elif file_type == "txt":
        data = extract_text_content(file)
        return data
    else:
        return "File type not allowed"


def delete_old_file(instance, field_name):
    field = getattr(instance, field_name, None)
    if field and field.name:
        field.delete(save=False)


def determine_attendance_type(leave_data):
    """Determine single attendance status based on leave type and available balances."""
    if not leave_data or not leave_data.leave_type:
        return constants.UNPAID_LEAVE

    leave_code = leave_data.leave_type.code
    leave_balance = get_leave_balance_for_date(
        leave_data.employee, leave_data.from_date
    )

    if leave_code == constants.HALFDAY_LEAVE:
        return "half_day"

    if leave_code == constants.SICK_LEAVE:
        if leave_balance:
            pending_sl = get_pending_quarter_sl(leave_balance, leave_data.from_date)
            if pending_sl > 0:
                return constants.PAID_LEAVE
        return constants.UNPAID_LEAVE

    # if leave_code == constants.PRIVILEGE_LEAVE:
    #     if not leave_balance:
    #         return constants.UNPAID_LEAVE

    #     current_month = leave_data.from_date.month
    #     monthly_pl_available = min(current_month, leave_balance.pl or 0)
    #     pending_pl = monthly_pl_available - (leave_balance.used_pl or 0)
    #     if pending_pl > 0:
    #         return constants.PAID_LEAVE
    #     return constants.UNPAID_LEAVE

    # return constants.UNPAID_LEAVE


def is_halfday_paid_leave(leave_data):
    """Check whether a half-day leave should be paid based on available PL."""
    if not leave_data or not leave_data.leave_type:
        return False

    leave_balance = get_leave_balance_for_date(
        leave_data.employee, leave_data.from_date
    )
    if not leave_balance:
        return False

    pending_pl = get_pending_monthly_pl(leave_balance, leave_data.from_date)
    return pending_pl >= 0.5


def determine_attendance_statuses(leave_data, total_days):
    """
    Determine attendance status per day for a leave request.

    For PL, if partial balance is available, mark earliest days as paid and
    remaining days as unpaid.
    """
    day_count = int(math.ceil(float(total_days or 0)))
    if not leave_data or not leave_data.leave_type:
        return [constants.UNPAID_LEAVE] * day_count

    leave_code = leave_data.leave_type.code

    if leave_code == constants.HALFDAY_LEAVE:
        return ["half_day"] * day_count

    if leave_code == constants.SICK_LEAVE:
        leave_balance = get_leave_balance_for_date(
            leave_data.employee, leave_data.from_date
        )
        if not leave_balance:
            return [constants.UNPAID_LEAVE] * day_count

        pending_sl = get_pending_quarter_sl(leave_balance, leave_data.from_date)
        statuses = []
        remaining_days = float(total_days)
        while remaining_days > 0:
            if pending_sl >= 1 or (pending_sl > 0 and remaining_days <= pending_sl):
                statuses.append(constants.PAID_LEAVE)
                pending_sl -= 1
            else:
                statuses.append(constants.UNPAID_LEAVE)
            remaining_days -= 1
        return statuses

    if leave_code != constants.PRIVILEGE_LEAVE:
        return [determine_attendance_type(leave_data)] * day_count

    leave_balance = get_leave_balance_for_date(
        leave_data.employee, leave_data.from_date
    )
    if not leave_balance:
        return [constants.UNPAID_LEAVE] * float(total_days)

    pending_pl = get_pending_monthly_pl(leave_balance, leave_data.from_date)

    statuses = []
    remaining_days = float(total_days)
    while remaining_days > 0:
        if pending_pl >= 1:
            statuses.append(constants.PAID_LEAVE)
            pending_pl -= 1
        else:
            statuses.append(constants.UNPAID_LEAVE)
        remaining_days -= 1

    return statuses


def get_pending_quarter_sl(leave_balance, leave_date):
    current_month = leave_date.month
    quarter = (current_month - 1) // 3 + 1
    allowed_sl = min(quarter, leave_balance.sl or 0)
    pending_sl = allowed_sl - (leave_balance.used_sl or 0)
    return max(0, pending_sl)


def get_leave_balance_for_date(employee, leave_date):
    return LeaveBalance.objects.filter(employee=employee, year=leave_date.year).first()


def get_pending_monthly_pl(leave_balance, leave_date):
    current_month = leave_date.month
    monthly_pl_available = min(current_month, leave_balance.pl or 0)
    pending_pl = monthly_pl_available - (leave_balance.used_pl or 0)
    return max(0, pending_pl)


def apply_pl_usage(leave_balance, pending_pl, count):
    if pending_pl >= count:
        leave_balance.used_pl += count
    else:
        if pending_pl > 0:
            leave_balance.used_pl += pending_pl
            leave_balance.used_lop += count - pending_pl
        else:
            leave_balance.used_lop += count
