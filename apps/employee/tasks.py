from celery import shared_task
from django.utils import timezone

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.employee.models import LeaveBalance
from apps.notification.models import NotificationType
from apps.notification.services import create_notification
from apps.superadmin import models


@shared_task
def credit_new_year_employee_leaves():
    print("🔥 CELERY BEAT TRIGGERED 🔥")
    current_year = timezone.now().year
    new_year = current_year + 1

    employees = models.Users.objects.filter(is_active=True)
    for employee in employees:
        leaves = LeaveBalance.objects.get_or_create(
            year=new_year, pl=12, sl=4, lop=0, employee=employee
        )
        print(leaves)

        print("done------------==============")
    return "Task cron completed successfully...."


@shared_task
def update_employee_absent_leaves():
    print("this function of employee absent triggered.....")
    today = timezone.now().date()
    present_employee_ids = EmployeeAttendance.objects.filter(day=today).values_list(
        "employee_id", flat=True
    )
    employees_left = models.Users.objects.filter(is_active=True).exclude(
        id__in=present_employee_ids
    )
    attendance_objects = [
        EmployeeAttendance(employee=employee, day=today, status=constants.UNPAID_LEAVE)
        for employee in employees_left
    ]
    EmployeeAttendance.objects.bulk_create(attendance_objects)
    print("done------------==============")
    return "Absent Employees attendance added successfully..."


@shared_task
def notify_employee_birthday():
    print("this birthday notify function called .....")
    today = timezone.now().date()
    employee_birthday_today = models.Users.objects.filter(
        is_active=True, birthdate__day=today.day, birthdate__month=today.month
    )
    if not employee_birthday_today.exists():
        return "No birthdays today"

    recipients = models.Users.objects.filter(is_active=True)
    for birthday_employee in employee_birthday_today:
        for recipient in recipients.exclude(id=birthday_employee.id):
            notification_type = NotificationType.objects.get(code=constants.BIRTHDAY)
            create_notification(
                recipient=recipient,
                actor=birthday_employee,
                notification_type=notification_type,
                title="🎉 Birthday Alert!",
                message=f"Today is {birthday_employee.first_name} {birthday_employee.last_name}'s birthday. Wish them!",
                related_object=birthday_employee,
            )
