from datetime import timedelta
from decimal import Decimal

# from weasyprint import HTML
import xhtml2pdf
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from apps.employee.models import LeaveBalance
from apps.superadmin.models import Leave


def weekdays_count(start_date, end_date):
    count = 0
    current = start_date

    while current <= end_date:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)

    print(f"==>> count: {count}")
    return count


def calculate_extra_leaves(employee):
    # today = timezone.now()
    year = timezone.now().year
    current_month = timezone.now().month

    # Will change this to filter().first() once whole flow is ready.
    leave_balance = LeaveBalance.objects.filter(
        employee=employee,
        year=year,
    ).first()
    if not leave_balance:
        return {"pl_leave": 0, "sl_leave": 0}

    approved_pl = min(current_month, leave_balance.pl)
    used_pl = leave_balance.used_pl or 0
    available_pl = max(approved_pl - used_pl, 0)
    print(f"==>> available_pl: {available_pl}")

    total_sl = leave_balance.sl or 0
    used_sl = leave_balance.used_sl or 0
    available_sl = max(total_sl - used_sl, 0)
    print(f"==>> available_sl: {available_sl}")

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
    print(f"==>> leaves: {leaves}")

    total_leave_days = 0

    for leave in leaves:
        if leave.to_date:
            leave_start = max(leave.from_date, start_date)
            leave_end = min(leave.to_date, end_date)
            total_leave_days += weekdays_count(leave_start, leave_end)
        else:
            total_leave_days += 1
    print(f"==>> total_leave_days: {total_leave_days}")

    leave_balance = calculate_extra_leaves(employee)
    print(f"==>> leave_balance: {leave_balance}")
    available_leaves = leave_balance["pl_leave"] + leave_balance["sl_leave"]

    extra_leave_days = max(total_leave_days - available_leaves, 0)
    print(f"==>> extra_leave_days: {extra_leave_days}")

    if extra_leave_days == 0:
        return Decimal("0.00")

    working_days = weekdays_count(start_date, end_date)
    print(f"==>> working_days: {working_days}")
    if working_days == 0:
        return Decimal("0.00")

    per_day_salary = (basic_salary + hr_allowance + special_allowance) / Decimal(
        working_days
    )

    leave_deduction = per_day_salary * Decimal(extra_leave_days)
    print(f"==>> leave_deduction: {leave_deduction}")
    return leave_deduction


def generate_payslip_pdf(payslip):
    html_string = render_to_string(
        "payslip.html",
        {
            "payslip": payslip,
            "company_name": "MultiMinds Technology Pvt Ltd",
        },
    )
    print(f"==>> html_string: {html_string}")

    # pdf = HTML(string=html_string).write_pdf()
    pdf = xhtml2pdf

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="payslip_{payslip.id}.pdf"'

    return response
