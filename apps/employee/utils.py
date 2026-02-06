import base64
import calendar
import os
from datetime import timedelta
from decimal import Decimal

import pdfkit

# from django.conf import settings
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from apps.attendance.models import EmployeeAttendance
from apps.attendance.utils import decimal_hours_to_hm
from apps.employee.models import LeaveBalance
from apps.superadmin.models import CommonData, Holiday, Leave

# from io import BytesIO


def holidays_in_month(year, month):
    return Holiday.objects.filter(date__year=year, date__month=month).count()


def weekdays_count(start_date, end_date):
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def calculate_extra_leaves(employee):
    year = timezone.now().year
    current_month = timezone.now().month

    leave_balance = LeaveBalance.objects.filter(
        employee=employee,
        year=year,
    ).first()
    if not leave_balance:
        return {"pl_leave": 0, "sl_leave": 0}

    approved_pl = min(current_month, leave_balance.pl)
    used_pl = leave_balance.used_pl or 0
    available_pl = max(approved_pl - used_pl, 0)

    total_sl = leave_balance.sl or 0
    used_sl = leave_balance.used_sl or 0
    available_sl = max(total_sl - used_sl, 0)

    return {
        "pl_leave": available_pl,
        "sl_leave": available_sl,
    }


def calculate_leave_deduction(
    employee, start_date, end_date, basic_salary, hr_allowance, special_allowance
):
    leaves = Leave.objects.filter(
        employee=employee,
        status="approved",
    ).filter(
        Q(from_date__lte=end_date)
        & Q(
            Q(to_date__gte=start_date)
            | Q(to_date__isnull=True, from_date__gte=start_date)
        )
    )

    total_leave_days = 0

    for leave in leaves:
        if leave.to_date:
            leave_start = max(leave.from_date, start_date)
            leave_end = min(leave.to_date, end_date)
            total_leave_days += weekdays_count(leave_start, leave_end)
        else:
            total_leave_days += 1

    leave_balance = calculate_extra_leaves(employee)
    available_leaves = leave_balance["pl_leave"] + leave_balance["sl_leave"]

    extra_leave_days = max(total_leave_days - available_leaves, 0)

    if extra_leave_days == 0:
        return Decimal("0.00")

    working_days = weekdays_count(start_date, end_date)
    if working_days == 0:
        return Decimal("0.00")

    per_day_salary = (basic_salary + hr_allowance + special_allowance) / Decimal(
        working_days
    )

    leave_deduction = per_day_salary * Decimal(extra_leave_days)
    return leave_deduction


def employee_monthly_working_hours(employee):
    today = timezone.now().date()
    year = today.year
    month = today.month
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(year, month)[1])

    working_days = weekdays_count(month_start, month_end)

    monthly_holidays = (
        Holiday.objects.filter(date__year=year, date__month=month)
        .exclude(date__week_day__in=[1, 7])
        .count()
    )

    monthly_leaves = Leave.objects.filter(
        employee=employee,
        status="approved",
        from_date__year=year,
        from_date__month=month,
    ).count()

    total_working_days = max(working_days - (monthly_holidays + monthly_leaves), 0)

    total_working_hours = total_working_days * 8

    working_days_till_today = weekdays_count(month_start, today)

    holidays_till_today = Holiday.objects.filter(
        date__lt=today,
        date__year=year,
        date__month=month,
    ).count()

    leaves_till_today = Leave.objects.filter(
        employee=employee,
        status="approved",
        from_date__lt=today,
        from_date__year=year,
        from_date__month=month,
    ).count()

    total_working_days_till_date = max(
        working_days_till_today - (holidays_till_today + leaves_till_today), 0
    )

    total_working_hours_till_date = (
        EmployeeAttendance.objects.filter(
            employee_id=employee.id,
            day__year=year,
            day__month=month,
        )
        .aggregate(total=Sum("work_hours"))
        .get("total")
        or 0
    )

    remaining_working_days = max(total_working_days - total_working_days_till_date, 0)

    daily_average_hours = decimal_hours_to_hm(
        total_working_hours_till_date / total_working_days_till_date
        if total_working_days_till_date > 0
        else 0
    )

    progress_percentage = (
        (total_working_hours_till_date / total_working_hours) * 100
        if total_working_hours > 0
        else 0
    )
    pending_hours = decimal_hours_to_hm(
        int(total_working_hours) - int(total_working_hours_till_date)
    )
    print(f"==>> pending_hours: {pending_hours}")
    return {
        "employee_email": employee.email,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "total_working_hours": total_working_hours,
        "pending_hours": pending_hours,
        "worked_hours": decimal_hours_to_hm(total_working_hours_till_date),
        "total_working_days": total_working_days,
        "remaining_working_days": remaining_working_days,
        "daily_average_hours": daily_average_hours,
        "progress_percentage": round(progress_percentage, 2),
    }


def imagefield_to_base64(image_field):
    if not image_field:
        return None

    try:
        with image_field.open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("Image base64 error:", e)
        return None


def generate_payslip_pdf_bytes(payslip):
    company = CommonData.objects.first()
    company_logo_base64 = imagefield_to_base64(
        company.company_logo if company else None
    )

    gross_salary = (
        (payslip.basic_salary or 0)
        + (payslip.hr_allowance or 0)
        + (payslip.special_allowance or 0)
    ) - payslip.total_deductions

    context = {
        "payslip": payslip,
        "employee": payslip.employee,
        "company_logo": company_logo_base64,
        "company_name": "MultiMinds Technology Pvt Ltd",
        "gross_salary": gross_salary,
    }

    html = render_to_string("payslip.html", context)

    options = {
        "page-size": "A4",
        "margin-top": "20mm",
        "margin-right": "15mm",
        "margin-bottom": "20mm",
        "margin-left": "15mm",
        "encoding": "UTF-8",
        "no-outline": None,
        "enable-local-file-access": None,
        "print-media-type": None,
    }

    config = None
    possible_paths = [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            config = pdfkit.configuration(wkhtmltopdf=path)
            break

    pdf = pdfkit.from_string(html, False, options=options, configuration=config)

    if not pdf:
        raise Exception("PDF generation failed - empty content")

    return pdf


def generate_payslip_pdf(payslip):
    try:
        pdf = generate_payslip_pdf_bytes(payslip)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="payslip_{payslip.id}.pdf"'
        )
        response["Content-Length"] = len(pdf)
        response["Cache-Control"] = "no-cache"
        return response

    except Exception as e:
        print(f"PDF generation error: {e}")
        return HttpResponse(
            f"PDF generation failed: {str(e)}", content_type="text/plain", status=500
        )


def is_weekend(date):
    return date.weekday() >= 5


def is_non_working(date, holiday_dates):
    return is_weekend(date) or date in holiday_dates


def calculate_leaves_with_sandwich(leave):
    """Calculate total leave days with sandwich rule applied."""
    if not leave.from_date:
        return 0, False

    if not leave.to_date:
        return 1, False

    holidays = Holiday.objects.filter(
        date__gte=leave.from_date,
        date__lte=leave.to_date,
        date__week_day__in=[1, 2, 3, 4, 5],
    )
    holiday_dates = set(h.date for h in holidays)

    start = leave.from_date
    end = leave.to_date
    if start == end:
        return 1, False

    base_days = (end - start).days + 1

    # STEP 1: Check "between" sandwich (holiday/weekend inside range)
    current = start + timedelta(days=1)
    between_non_working = False

    while current < end:
        if is_non_working(current, holiday_dates):
            between_non_working = True
            break
        current += timedelta(days=1)

    if between_non_working:
        return base_days, True

    # STEP 2: Check chain sandwich (leave on both sides of non-working days)
    before = start - timedelta(days=1)
    after = end + timedelta(days=1)

    if is_non_working(before, holiday_dates) and is_non_working(after, holiday_dates):
        absorbed_start = start
        absorbed_end = end

        prev_day = before
        while is_non_working(prev_day, holiday_dates):
            absorbed_start = prev_day
            prev_day -= timedelta(days=1)

        next_day = after
        while is_non_working(next_day, holiday_dates):
            absorbed_end = next_day
            next_day += timedelta(days=1)

        total_days = (absorbed_end - absorbed_start).days + 1
        print(f"==>> total_days: {total_days}")
        return total_days, True

    # STEP 3: No sandwich
    print(f"==>> base_days: {base_days}")
    return base_days, False
