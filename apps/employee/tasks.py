from calendar import monthrange
from decimal import Decimal

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
from apps.employee.models import LeaveBalance, PaySlip
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
            notification_type = NotificationType.objects.filter(
                code=constants.BIRTHDAY
            ).first()
            create_notification(
                recipient=recipient,
                actor=birthday_employee,
                notification_type=notification_type,
                title="🎉 Birthday Alert!",
                message=f"Today is {birthday_employee.first_name} {birthday_employee.last_name}'s birthday. Wish them!",
                related_object=birthday_employee,
            )


@shared_task
def generate_monthly_payslips():
    """Auto-generate payslips on 5th of each month with leave deductions."""
    print("🔥 PAYSLIP GENERATION TASK TRIGGERED 🔥")

    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    # Calculate previous month
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    start_date = timezone.datetime(prev_year, prev_month, 1).date()
    end_date = timezone.datetime(
        prev_year, prev_month, monthrange(prev_year, prev_month)[1]
    ).date()
    month_name = start_date.strftime("%B %Y")
    common_data = models.CommonData.objects.first()
    employees = models.Users.objects.filter(
        role=constants.EMPLOYEE_USER, is_active=True
    )

    for employee in employees:
        if PaySlip.objects.filter(employee=employee, month=month_name).exists():
            continue

        leave_balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            year=current_year,
            defaults={
                "pl": common_data.pl_leave,
                "sl": common_data.sl_leave,
                "lop": common_data.lop_leave,
            },
        )

        leave_deduction = calculate_leave_deduction(
            employee, start_date, end_date, leave_balance
        )
        print(f"==>> leave_deduction: {leave_deduction}")

        basic_salary = employee.salary_ctc * Decimal("0.5")
        hr_allowance = basic_salary * Decimal("0.6")
        special_allowance = basic_salary * Decimal("0.4")
        total_earnings = basic_salary + hr_allowance + special_allowance

        tax_deductions = 200
        other_deductions = Decimal("0")
        total_deductions = tax_deductions + other_deductions + leave_deduction

        net_salary = total_earnings - total_deductions

        PaySlip.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            month=month_name,
            days=monthrange(prev_year, prev_month)[1],
            basic_salary=basic_salary,
            hr_allowance=hr_allowance,
            special_allowance=special_allowance,
            total_earnings=total_earnings,
            tax_deductions=tax_deductions,
            other_deductions=other_deductions,
            leave_deductions=leave_deduction,
            total_deductions=total_deductions,
            net_salary=net_salary,
        )

        print(f"Payslip generated for {employee.email} - {month_name}")

    return f"Payslips generated successfully for {month_name}"


def calculate_leave_deduction(employee, start_date, end_date, leave_balance):
    """Calculate leave deduction based on monthly PL allocation and SL usage."""
    leaves = models.Leave.objects.filter(
        employee=employee,
        status="approved",
    ).filter(
        Q(from_date__lte=end_date)
        & Q(
            Q(to_date__gte=start_date)
            | Q(to_date__isnull=True, from_date__gte=start_date)
        )
    )
    print(f"==>> leaves: {leaves}")

    total_leave_days = sum(float(leave.total_days or 0) for leave in leaves)

    if total_leave_days == 0:
        return Decimal("0")

    current_month = start_date.month
    monthly_pl_allocation = min(current_month, leave_balance.pl or 12)

    available_pl = monthly_pl_allocation - (leave_balance.used_pl or 0)
    available_sl = (leave_balance.sl or 4) - (leave_balance.used_sl or 0)

    deductible_days = 0
    remaining_days = total_leave_days

    if remaining_days > 0 and available_pl > 0:
        used_pl = min(remaining_days, available_pl)
        remaining_days -= used_pl
        leave_balance.used_pl = (leave_balance.used_pl or 0) + used_pl

    # Then use available SL
    if remaining_days > 0 and available_sl > 0:
        used_sl = min(remaining_days, available_sl)
        remaining_days -= used_sl
        # Update leave balance for SL usage
        leave_balance.used_sl = (leave_balance.used_sl or 0) + used_sl

    # Remaining days are LOP (deductible)
    if remaining_days > 0:
        deductible_days = remaining_days
        leave_balance.used_lop = (leave_balance.used_lop or 0) + deductible_days

    leave_balance.save()

    # Calculate per-day salary deduction
    daily_salary = (employee.salary_ctc or Decimal("0")) / 30
    leave_deduction = daily_salary * Decimal(str(deductible_days))

    return leave_deduction


def get_leave_deduction_preview(employee, start_date, end_date, leave_balance):
    """Get leave deduction preview without updating balance - for views only."""
    # Get approved leaves in the month
    leaves = (
        models.Leave.objects.filter(
            employee=employee,
            status="approved",
        )
        .filter(
            Q(from_date__lte=end_date)
            & Q(
                Q(to_date__gte=start_date)
                | Q(to_date__isnull=True, from_date__gte=start_date)
            )
        )
        .select_related("leave_type")
    )

    if not leaves.exists():
        return Decimal("0")

    # Monthly PL allocation (1 per month up to current month)
    current_month = start_date.month
    monthly_pl_allocation = min(current_month, leave_balance.pl or 12)

    # Available leaves (don't modify original balance)
    available_pl = monthly_pl_allocation - (leave_balance.used_pl or 0)
    available_sl = (leave_balance.sl or 4) - (leave_balance.used_sl or 0)

    # Separate leaves by type
    pl_days = 0
    sl_days = 0
    other_days = 0

    for leave in leaves:
        days = float(leave.total_days or 0)
        if leave.leave_type and leave.leave_type.code == constants.SICK_LEAVE:
            sl_days += days
        elif leave.leave_type and leave.leave_type.code in [
            constants.PRIVILEGE_LEAVE,
            constants.HALFDAY_LEAVE,
        ]:
            pl_days += days
        else:
            other_days += days

    # Calculate deductible days
    deductible_days = 0

    # Process SL first
    if sl_days > 0:
        if available_sl >= sl_days:
            available_sl -= sl_days
        else:
            deductible_days += sl_days - available_sl
            available_sl = 0

    # Process PL next
    if pl_days > 0:
        if available_pl >= pl_days:
            available_pl -= pl_days
        else:
            deductible_days += pl_days - available_pl
            available_pl = 0

    # Other leave types are always deductible
    deductible_days += other_days

    # Calculate per-day salary deduction
    daily_salary = (employee.salary_ctc or Decimal("0")) / 30
    print(f"==>> daily_salary: {daily_salary}")
    leave_deduction = daily_salary * Decimal(str(deductible_days))
    print(f"==>> leave_deduction: {leave_deduction}")

    return leave_deduction


@shared_task
def notify_frequent_late_comings():
    print("this function of frequent late comings triggered.....")
    today = timezone.now().date()
    office_time = timezone.timedelta(hours=10, minutes=30)
    print(f"==>> office_time: {office_time}")
    late_coming_employees = (
        EmployeeAttendance.objects.filter(day=today, check_in__gt=office_time)
        .select_related("employee")
        .values_list("employee", flat=True)
        .distinct()
    )
    print(f"==>> late_coming_employees: {late_coming_employees}")
    if not late_coming_employees.exists():
        return "No late comers today"

    recipients = models.Users.objects.filter(is_active=True, role="admin")
    print(f"==>> recipients: {recipients}")
    for late_coming_employee in late_coming_employees:
        for recipient in recipients.exclude(id=late_coming_employee.id):
            notification_type = NotificationType.objects.filter(
                code=constants.LATE_COMING
            ).first()
            create_notification(
                recipient=recipient,
                actor=late_coming_employee,
                notification_type=notification_type,
                title="🚨 Late Coming Alert!",
                message=(
                    f"{late_coming_employee.employee.first_name} "
                    f"{late_coming_employee.employee.last_name} is late today.",
                ),
                related_object=late_coming_employee,
            )
