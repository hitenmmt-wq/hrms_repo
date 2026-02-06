from calendar import monthrange
from datetime import time
from decimal import Decimal

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from apps.attendance.models import EmployeeAttendance
from apps.attendance.utils import check_out
from apps.base import constants
from apps.employee.models import LeaveBalance, PaySlip
from apps.employee.utils import (
    generate_payslip_pdf_bytes,
    holidays_in_month,
    weekdays_count,
)
from apps.notification.models import NotificationType
from apps.notification.services import create_notification
from apps.superadmin import models
from apps.superadmin.tasks import send_email_task


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
        present_days = 0
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
        attendance_data = EmployeeAttendance.objects.filter(
            employee=employee, day__month=current_month
        )
        print(f"==>> attendance_data: {attendance_data}")
        print(f"==>> attendance_data count: {attendance_data.count()}")
        for attendance in attendance_data:
            if attendance.status in ["paid_leave", "present", "incomplete_hours"]:
                present_days += 1
            elif attendance.status in ["half_day"]:
                if attendance.is_halfday_paid:
                    present_days += 0.5
        print(f"==>> present_days: {present_days}")

        basic_salary = employee.salary_ctc * Decimal("0.5")
        hr_allowance = basic_salary * Decimal("0.6")
        special_allowance = basic_salary * Decimal("0.4")
        total_earnings = basic_salary + hr_allowance + special_allowance

        tax_deductions = 200
        other_deductions = Decimal("0")
        total_deductions = tax_deductions + other_deductions + leave_deduction

        net_salary = total_earnings - total_deductions

        payslip = PaySlip.objects.create(
            employee=employee,
            start_date=start_date,
            end_date=end_date,
            month=month_name,
            days=present_days,
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

        # Send email to user with generated payslip PDF
        try:
            payslip_pdf = generate_payslip_pdf_bytes(payslip)
            send_email_task.delay(
                subject=f"Payment-Slip Generated for {payslip.month}",
                to_email=payslip.employee.email,
                text_body=(
                    f"Hi {payslip.employee.first_name} {payslip.employee.last_name},"
                    f"\n\nYour Payment-slip has been generated for {payslip.month}."
                    "\n\nYou can Download it from here."
                ),
                pdf_bytes=payslip_pdf,
                filename=f"payslip_{payslip.id}.pdf",
            )
        except Exception as e:
            print(f"Payslip email failed for {employee.email}: {e}")

        print(f"Payslip generated for {employee.email} - {month_name}")

    return f"Payslips generated successfully for {month_name}"


def calculate_leave_deduction(employee, start_date, end_date, leave_balance):
    """Calculate leave deduction based on leave types and monthly allocation - UPDATES BALANCE."""
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
    print(f"🔍 Payslip generation - leaves found: {leaves.count()}")

    if not leaves.exists():
        return Decimal("0")

    current_month = start_date.month
    monthly_pl_allocation = current_month

    # Available leaves
    available_pl = monthly_pl_allocation - (leave_balance.used_pl or 0)
    available_sl = (leave_balance.sl or 4) - (leave_balance.used_sl or 0)

    # Ensure available leaves don't go negative
    available_pl = max(0, available_pl)
    available_sl = max(0, available_sl)

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

    print(f"📊 Leave breakdown - PL: {pl_days}, SL: {sl_days}, Other: {other_days}")
    print(f"💰 Available - PL: {available_pl}, SL: {available_sl}")

    deductible_days = 0

    if sl_days > 0:
        if available_sl >= sl_days:
            leave_balance.used_sl = (leave_balance.used_sl or 0) + sl_days
        else:
            if available_sl > 0:
                leave_balance.used_sl = (leave_balance.used_sl or 0) + available_sl
                deductible_days += sl_days - available_sl
            else:
                deductible_days += sl_days

    if pl_days > 0:
        free_pl_per_month = 1
        if pl_days <= free_pl_per_month:
            leave_balance.used_pl = (leave_balance.used_pl or 0) + pl_days
        else:
            leave_balance.used_pl = (leave_balance.used_pl or 0) + pl_days
            excess_pl = pl_days - free_pl_per_month
            deductible_days += excess_pl

    if other_days > 0:
        deductible_days += other_days
        leave_balance.used_lop = (leave_balance.used_lop or 0) + other_days

    leave_balance.save()

    daily_salary = (employee.salary_ctc or Decimal("0")) / 30
    leave_deduction = daily_salary * Decimal(str(deductible_days))
    print(f"💸 Total deductible days: {deductible_days}, deduction: {leave_deduction}")

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
        return Decimal("0"), 0

    current_year = timezone.now().year
    current_month = timezone.now().month  # start_date.month
    monthly_pl_allocation = current_month  # 1 PL per month
    print(f"==>> monthly_pl_allocation: {monthly_pl_allocation}")

    available_pl = monthly_pl_allocation - (leave_balance.used_pl or 0)
    available_sl = (leave_balance.sl or 4) - (leave_balance.used_sl or 0)

    available_pl = max(0, available_pl)
    available_sl = max(0, available_sl)

    pl_days = 0
    sl_days = 0
    other_days = 0

    print(f"==>> leaves: {leaves}")
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

    print(f"==>> available_pl: {available_pl}, available_sl: {available_sl}")
    print(f"==>> pl_days: {pl_days}, sl_days: {sl_days}, other_days: {other_days}")

    deductible_days = 0

    if sl_days > 0:
        if available_sl >= sl_days:
            available_sl -= sl_days
        else:
            deductible_days += sl_days - available_sl
            available_sl = 0

    # Process PL next - 1 PL free per month, excess deducted
    if pl_days > 0:
        free_pl_per_month = 1  # 1 PL is free per month
        if pl_days <= free_pl_per_month:
            # All PL covered (1 or less)
            print(f"✅ All {pl_days} PL days covered (free allowance)")
        else:
            # More than 1 PL - deduct excess
            excess_pl = pl_days - free_pl_per_month
            deductible_days += excess_pl
            print(f"⚠️ PL: {free_pl_per_month} free, {excess_pl} excess deducted")

    # Other leave types are always deductible
    deductible_days += other_days

    holidays = holidays_in_month(current_year, current_month)
    working_days = weekdays_count(start_date, end_date) - holidays
    # Calculate per-day salary deduction
    daily_salary = (employee.salary_ctc or Decimal("0")) / working_days
    leave_deduction = daily_salary * Decimal(str(deductible_days))
    print(f"==>> daily_salary: {daily_salary}, leave_deduction: {leave_deduction}")

    return leave_deduction, deductible_days


def get_leave_balance_details(employee, start_date, end_date):
    """Get detailed leave balance information for employee between dates."""

    # Get or create leave balance for the year
    year = start_date.year
    leave_balance, _ = LeaveBalance.objects.get_or_create(employee=employee, year=year)

    # Get approved leaves in the date range
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

    # Calculate monthly usage from date range
    monthly_pl = monthly_sl = monthly_lop = 0
    for leave in leaves:
        days = float(leave.total_days or 0)
        if leave.leave_type and leave.leave_type.code == constants.SICK_LEAVE:
            monthly_sl += days
        elif leave.leave_type and leave.leave_type.code in [
            constants.PRIVILEGE_LEAVE,
            constants.HALFDAY_LEAVE,
        ]:
            monthly_pl += days
        else:
            monthly_lop += days

    # Monthly PL allocation - 1 per month up to current month (cumulative)
    current_month = start_date.month
    total_pl_allocated = current_month  # Total PL available up to this month

    # Calculate used leaves by type from database
    used_pl = leave_balance.used_pl or 0
    used_sl = leave_balance.used_sl or 0
    used_lop = leave_balance.used_lop or 0
    print(f"==>> used_lop: {used_lop}")

    # Calculate available leaves
    total_sl_allocated = leave_balance.sl or 4
    available_pl = max(0, total_pl_allocated - used_pl)
    print(f"==>> available_pl: {available_pl}")
    available_sl = max(0, total_sl_allocated - used_sl)
    print(f"==>> available_sl: {available_sl}")

    return {
        "monthly": {
            "pl": {
                "total": current_month,
                "used": monthly_pl,
                "available": max(0, current_month - (monthly_pl or 0)),
            },
            "sl": {
                "total": leave_balance.sl or 4,
                "used": monthly_sl,
                "available": max(0, (leave_balance.sl or 4) - (monthly_sl or 0)),
            },
            "lop": {
                "total": 0,
                "used": abs(current_month - monthly_pl),
                "available": 0,
            },
        },
        "yearly": {
            "pl": {
                "total": 12,
                "used": leave_balance.used_pl or 0,
                "available": max(0, 12 - (leave_balance.used_pl or 0)),
            },
            "sl": {
                "total": leave_balance.sl or 4,
                "used": leave_balance.used_sl or 0,
                "available": max(
                    0, (leave_balance.sl or 4) - (leave_balance.used_sl or 0)
                ),
            },
            "lop": {"total": 0, "used": leave_balance.used_lop or 0, "available": 0},
        },
    }


@shared_task
def notify_frequent_late_comings():
    print("this function of frequent late comings triggered.....")
    today = timezone.now().date()
    office_time = time(hour=10, minute=30)
    print(f"==>> office_time: {office_time}")
    late_coming_employees = (
        EmployeeAttendance.objects.filter(
            day=today, check_in__time__gt=str(office_time)
        )
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
        for recipient in recipients.exclude(id=late_coming_employee):
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


@shared_task
def auto_checkout_employees():
    print("this function of auto checkout triggered.....")
    today = timezone.now().date()
    employees_to_checkout = EmployeeAttendance.objects.filter(
        day=today, check_in__isnull=False, check_out__isnull=True
    )
    previous_employee_tocheckout = EmployeeAttendance.objects.filter(
        day__lt=today, check_in__isnull=False, check_out__isnull=True
    )
    print(f"==>> employees_to_checkout: {employees_to_checkout}")
    print(f"==>> previous_employee_tocheckout: {previous_employee_tocheckout}")
    for attendance in previous_employee_tocheckout:
        check_out(attendance)
        print(f"Auto checked out {attendance.employee.email} for previous pending days")
    for attendance in employees_to_checkout:
        check_out(attendance)
        print(f"Auto checked out {attendance.employee.email} for {today}")

    return "Auto checkout completed for employees."


@shared_task
def notify_employee_next_holiday():
    print("-------This function called to notify employee on next holiday----")
    today = timezone.now().date()
    next_day = today + timezone.timedelta(days=1)
    next_holiday = (
        models.Holiday.objects.filter(date__gte=today).order_by("date").first()
    )

    if next_holiday is None:
        return "No holiday found"

    if next_holiday.date != next_day:
        return "No holiday found on next day"

    if next_holiday.date == next_day:
        receipents = models.Users.objects.filter(is_active=True)
        notification_type = NotificationType.objects.filter(
            code=constants.NEXT_DAY_HOLIDAY
        ).first()
        for receipent in receipents:
            create_notification(
                recipient=receipent,
                notification_type=notification_type,
                title="🎉 Holiday Reminder!",
                message=f"Upcoming holiday {next_holiday.name} is on {next_holiday.date}. Make sure to make it count.",
                related_object=next_holiday,
            )
