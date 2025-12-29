import base64
import calendar
import os
from datetime import date, timedelta
from decimal import Decimal

import pdfkit

# from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from apps.employee.models import LeaveBalance
from apps.superadmin.models import CommonData, Holiday, Leave

# from io import BytesIO


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
    year = timezone.now().year
    current_month = timezone.now().month

    # TOTAL HOURS CALCULATIONS
    working_days = weekdays_count(
        date.today().replace(day=1),
        date.today().replace(
            day=calendar.monthrange(date.today().year, date.today().month)[1]
        ),
    )
    monthly_holiday_list = Holiday.objects.filter(
        date__month=current_month, date__year=year
    ).count()
    employees_leave = Leave.objects.filter(
        employee=employee,
        status="approved",
        from_date__year=year,
        from_date__month=current_month,
    ).count()

    total_working_days = working_days - (monthly_holiday_list + employees_leave)
    total_working_hours = total_working_days * 8

    # WORKED HOURS CALCULATIONS

    working_days_currently = weekdays_count(date.today().replace(day=1), today) - 1
    monthly_holiday_currently = Holiday.objects.filter(
        date__lt=today, date__year=year
    ).count()
    employees_leave_currently = Leave.objects.filter(
        employee=employee,
        status="approved",
        from_date__lt=today,
    ).count()

    total_working_days_till_date = working_days_currently - (
        monthly_holiday_currently + employees_leave_currently
    )
    total_working_hours_till_date = total_working_days_till_date * 8

    remaining_working_days = total_working_days - total_working_days_till_date

    daily_average_hours = (
        total_working_hours_till_date / total_working_days_till_date
        if total_working_days_till_date > 0
        else 0
    )

    progress_percentage = (total_working_hours_till_date / total_working_hours) * 100

    monthly_working_hours_data = {
        "total_working_hours": total_working_hours,
        "worked_hours": total_working_hours_till_date,
        "total_working_days": total_working_days,
        "remaining_working_days": remaining_working_days,
        "daily_average_hours": daily_average_hours,
        "progress_percentage": progress_percentage,
    }
    return monthly_working_hours_data


def imagefield_to_base64(image_field):
    if not image_field:
        return None

    try:
        with image_field.open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print("Image base64 error:", e)
        return None


def generate_payslip_pdf(payslip):
    company = CommonData.objects.first()
    company_logo_base64 = imagefield_to_base64(
        company.company_logo if company else None
    )

    gross_salary = (
        (payslip.basic_salary or 0)
        + (payslip.hr_allowance or 0)
        + (payslip.special_allowance or 0)
    )

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

    try:
        pdf = pdfkit.from_string(html, False, options=options, configuration=config)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="payslip_{payslip.id}.pdf"'
        )
        return response

    except Exception as e:
        print(f"PDF generation error: {e}")
        return HttpResponse(html, content_type="text/html")
