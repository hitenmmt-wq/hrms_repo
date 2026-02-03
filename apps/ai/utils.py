from datetime import date, timedelta

from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import ExtractMonth, ExtractWeekDay
from django.utils import timezone

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.employee.models import LeaveBalance, PaySlip
from apps.superadmin import models


class PromptTemplates:
    """Collection of prompt templates for different intents and roles."""

    SYSTEM_CONTEXT = {
        "general": """
            - You have to use timezone as stored in Database.
            - You are an AI assistant integrated with HRMS system.
            - Your purpose is to help users with HR-related queries.
            - Always maintain professionalism and confidentiality.
            - Do not make up information; only use provided data.
            - If unsure, ask for clarification.
            - If passing any data of image, then try to display image
              else dont show at all, because url_path is not ideal showing to user.
        """,
        "employee": """You are a helpful HRMS Assistant for employees.
            You assist with:
            - Leave balance and application status
            - Attendance records and statistics
            - Payslip information
            - Personal profile information
            - General HR policies and procedures

            Rules:
            1. Only show the user their own data
            2. Be concise and friendly
            3. If data is not available, suggest checking the HRMS system directly
            4. Never provide other employees' data
            5. Use simple, non-technical language""",
        "hr": """You are an HR Assistant for HR personnel.
            You help with:
            - Leave management (pending, approved, rejected applications)
            - Employee information and search
            - Attendance tracking and analytics
            - Payroll summaries
            - Company policies and procedures
            - Department and position information

            Rules:
            1. You can access all employee data
            2. Provide insights and summaries
            3. Help with decision-making
            4. Be professional and detail-oriented
            5. Highlight important trends or issues""",
        "admin": """You are the HRMS System Administrator Assistant.
            You have full access to:
            - All employee and company data
            - System analytics and reports
            - Configuration information
            - Access logs and activity
            - Performance metrics

            Rules:
            1. You have full system access
            2. Provide comprehensive data and insights
            3. Help with system management and optimization
            4. Highlight critical issues
            5. Provide technical details when relevant""",
    }

    LEAVE_INQUIRY = """Based on the provided leave information:
        - Summarize current leave balance
        - Mention any pending applications
        - Provide recent leave history if available
        - Answer the user's specific question about leaves"""

    ATTENDANCE_INQUIRY = """Based on the provided attendance information:
        - Show recent attendance status
        - Calculate and mention attendance percentage
        - Highlight any patterns or issues
        - Answer the user's specific question about attendance"""

    PAYROLL_INQUIRY = """Based on the provided payroll information:
        - Summarize recent payslips
        - Show salary information if available
        - Mention any payment status
        - Answer the user's specific question about payroll"""

    PROFILE_INQUIRY = """Based on the provided profile information:
        - Confirm user's personal details
        - Show department and position
        - Mention employment status
        - Answer the user's specific question about their profile"""

    GENERAL_INQUIRY = """Based on the provided company information:
        - Share relevant company data and policies
        - Provide insights and statistics
        - Suggest relevant resources or procedures
        - Answer the user's specific question clearly"""

    GREETING = """Respond warmly and helpfully:
        - Greet the user appropriately
        - Brief introduction of your capabilities
        - Ask how you can help
        - Keep it friendly and professional"""

    IRRELEVENT = """
        - This are irrelevent question.
        - Questions should be avoided and tell to ask regarding HRMS portal.
        - Explain that you are not answerable to that and ask for some relevent question only.
        - Tell user to be clear with their questions.
    """

    @classmethod
    def get_template_for_intent(cls, intent: str) -> str:
        """Get the appropriate prompt template for an intent."""
        templates = {
            "leave_inquiry": cls.LEAVE_INQUIRY,
            "attendance_inquiry": cls.ATTENDANCE_INQUIRY,
            "payroll_inquiry": cls.PAYROLL_INQUIRY,
            "profile_inquiry": cls.PROFILE_INQUIRY,
            "general_inquiry": cls.GENERAL_INQUIRY,
            "greeting": cls.GREETING,
            "irrelevent": cls.IRRELEVENT,
            "hr_analytics": """Based on the provided HR data:
                - Provide comprehensive analytics
                - Highlight trends and patterns
                - Mention key metrics
                - Answer the user's specific question""",
            "company_info": """Based on the provided company information:
                - Share relevant company details
                - Provide organizational context
                - Mention policies if relevant
                - Answer the user's specific question""",
        }
        return templates.get(intent, cls.GENERAL_INQUIRY)


def calculate_leave_patterns():
    today = timezone.now().date()
    current_year = today.year

    leaves = models.Leave.objects.filter(from_date__year=current_year)

    balances = LeaveBalance.objects.filter(year=current_year)

    if not leaves.exists():
        return {"message": "No leave data found for this year."}

    total_leaves = leaves.count()

    status_distribution = leaves.values("status").annotate(count=Count("id"))

    status_summary = {s["status"]: s["count"] for s in status_distribution}

    leave_type_distribution = leaves.values("leave_type__code").annotate(
        count=Count("id"), total_days=Sum("total_days")
    )

    leave_types = {
        leav["leave_type__code"]
        or "unknown": {
            "applications": leav["count"],
            "total_days": float(leav["total_days"] or 0),
        }
        for leav in leave_type_distribution
    }

    sandwich_leaves = leaves.filter(is_sandwich_applied=True)

    sandwich_summary = {
        "sandwich_leave_count": sandwich_leaves.count(),
        "sandwich_leave_days": float(
            sandwich_leaves.aggregate(total=Sum("total_days"))["total"] or 0
        ),
        "sandwich_percentage": (
            round((sandwich_leaves.count() / total_leaves) * 100, 2)
            if total_leaves
            else 0
        ),
    }

    month_distribution = (
        leaves.annotate(month=ExtractMonth("from_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    month_wise = {m["month"]: m["count"] for m in month_distribution}

    balance_summary = balances.aggregate(
        total_pl=Sum("pl"),
        used_pl=Sum("used_pl"),
        total_sl=Sum("sl"),
        used_sl=Sum("used_sl"),
        total_lop=Sum("lop"),
        used_lop=Sum("used_lop"),
    )

    utilization = {
        "pl_utilization_percent": (
            round((balance_summary["used_pl"] / balance_summary["total_pl"]) * 100, 2)
            if balance_summary["total_pl"]
            else 0
        ),
        "sl_utilization_percent": (
            round((balance_summary["used_sl"] / balance_summary["total_sl"]) * 100, 2)
            if balance_summary["total_sl"]
            else 0
        ),
        "lop_utilization_percent": (
            round((balance_summary["used_lop"] / balance_summary["total_lop"]) * 100, 2)
            if balance_summary["total_lop"]
            else 0
        ),
    }

    low_pl_balance = balances.filter(pl__gt=0, used_pl__gte=F("pl") * 0.8).count()

    lop_heavy_users = balances.filter(used_lop__gt=5).count()

    context = {
        "leave_volume": {
            "total_applications": total_leaves,
            "status_distribution": status_summary,
        },
        "leave_type_patterns": leave_types,
        "sandwich_patterns": sandwich_summary,
        "month_wise_distribution": month_wise,
        "leave_balance_utilization": utilization,
        "risk_indicators": {
            "employees_low_on_pl": low_pl_balance,
            "lop_heavy_users": lop_heavy_users,
        },
    }
    print(f"==>> context: {context}")
    return context


def calculate_attendance_patterns():
    today = timezone.now().date()
    year_start = date(today.year, 1, 1)
    year_end = date(today.year, 12, 31)

    attendance_qs = EmployeeAttendance.objects.filter(day__range=(year_start, year_end))

    if not attendance_qs.exists():
        return {"message": "No attendance data found for this year."}

    total_records = attendance_qs.count()

    status_distribution = attendance_qs.values("status").annotate(count=Count("id"))

    status_summary = {s["status"]: s["count"] for s in status_distribution}

    month_distribution = (
        attendance_qs.annotate(month=ExtractMonth("day"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    month_wise = {m["month"]: m["count"] for m in month_distribution}

    hours_summary = attendance_qs.aggregate(
        avg_work_hours=Avg("work_hours"),
        avg_break_hours=Avg("break_hours"),
        total_work_hours=Sum("work_hours"),
        total_break_hours=Sum("break_hours"),
    )

    no_check_in = attendance_qs.filter(check_in__isnull=True).count()

    incomplete_days = attendance_qs.filter(
        check_in__isnull=False, check_out__isnull=True
    ).count()

    half_days = attendance_qs.filter(status="half_day").count()

    unpaid_leaves = attendance_qs.filter(status="unpaid_leave").count()

    break_logs = AttendanceBreakLogs.objects.filter(
        attendance__day__range=(year_start, year_end)
    )

    avg_breaks_per_day = (
        break_logs.values("attendance")
        .annotate(count=Count("id"))
        .aggregate(avg=Avg("count"))["avg"]
    )

    long_breaks = (
        break_logs.filter(
            pause_time__isnull=False,
            restart_time__isnull=False,
            restart_time__gt=F("pause_time"),
        )
        .extra(where=["EXTRACT(EPOCH FROM (restart_time - pause_time)) / 60 > 60"])
        .count()
    )

    paused_not_resumed = break_logs.filter(
        pause_time__isnull=False, restart_time__isnull=True
    ).count()

    context = {
        "attendance_volume": {
            "total_records": total_records,
            "status_distribution": status_summary,
        },
        "month_wise_distribution": month_wise,
        "work_hour_patterns": {
            "average_work_hours": (
                round(hours_summary["avg_work_hours"], 2)
                if hours_summary["avg_work_hours"]
                else 0
            ),
            "average_break_hours": (
                round(hours_summary["avg_break_hours"], 2)
                if hours_summary["avg_break_hours"]
                else 0
            ),
            "total_work_hours": hours_summary["total_work_hours"] or 0,
            "total_break_hours": hours_summary["total_break_hours"] or 0,
        },
        "behavior_patterns": {
            "missing_check_in_days": no_check_in,
            "incomplete_days": incomplete_days,
            "half_days": half_days,
            "unpaid_leaves": unpaid_leaves,
        },
        "break_patterns": {
            "average_breaks_per_day": (
                round(avg_breaks_per_day, 2) if avg_breaks_per_day else 0
            ),
            "long_breaks_over_1hr": long_breaks,
            "paused_not_resumed": paused_not_resumed,
        },
    }
    print(f"==>> context: {context}")
    return context


def calculate_payroll_patterns():
    today = timezone.now().date()
    year_start = date(today.year, 1, 1)
    year_end = date(today.year, 12, 31)
    payrolls = PaySlip.objects.filter(
        start_date__lte=year_end, end_date__gte=year_start
    )
    payroll_count = payrolls.count()

    employees_paid = payrolls.values("employee").distinct().count()

    month_distribution = (
        payrolls.annotate(month_num=ExtractMonth("start_date"))
        .values("month_num")
        .annotate(count=Count("id"))
        .order_by("month_num")
    )

    payroll_months = {m["month_num"]: m["count"] for m in month_distribution}

    missing_months = [m for m in range(1, 13) if m not in payroll_months]

    earnings = payrolls.aggregate(
        total_earning=Sum("total_earnings"),
        avg_earnings=Avg("total_earnings"),
        total_net=Sum("net_salary"),
        avg_net=Avg("net_salary"),
        total_deductions=Sum("total_deductions"),
    )

    deduction_percentage = None
    if earnings["total_earning"] and earnings["total_deductions"]:
        deduction_percentage = round(
            (earnings["total_deductions"] / earnings["total_earning"]) * 100, 2
        )

    structure = payrolls.aggregate(
        basic=Sum("basic_salary"),
        hra=Sum("hr_allowance"),
        special=Sum("special_allowance"),
        leave_deduction=Sum("leave_deductions"),
    )

    high_deduction_payslips = payrolls.filter(
        total_deductions__gt=0.4 * float((earnings["avg_earnings"] or 1))
    ).count()

    zero_net_salary = payrolls.filter(net_salary__lte=0).count()

    context = {
        "payroll_count": payroll_count,
        "employees_paid": employees_paid,
        "month_wise_distribution": payroll_months,
        "missing_payroll_months": missing_months,
        "earnings_summary": {
            "total_earnings": (
                round(earnings["total_earning"], 2) if earnings["total_earning"] else 0
            ),
            "average_earnings": (
                round(earnings["avg_earnings"], 2) if earnings["avg_earnings"] else 0
            ),
            "total_net_salary": (
                round(earnings["total_net"], 2) if earnings["total_net"] else 0
            ),
            "average_net_salary": (
                round(earnings["avg_net"], 2) if earnings["avg_net"] else 0
            ),
            "total_deductions": (
                round(earnings["total_deductions"], 2)
                if earnings["total_deductions"]
                else 0
            ),
            "deduction_percentage": deduction_percentage,
        },
        "salary_structure": {
            "basic_salary_total": structure["basic"],
            "hra_total": structure["hra"],
            "special_allowance_total": structure["special"],
            "leave_deductions_total": structure["leave_deduction"],
        },
        "risk_indicators": {
            "high_deduction_payslips": high_deduction_payslips,
            "zero_net_salary_payslips": zero_net_salary,
        },
    }
    print(f"==>> context: {context}")
    return context


def calculate_profile_patterns():
    today = timezone.now().date()
    users = models.Users.objects.filter(is_active=True)

    if not users.exists():
        return {"message": "No active users found."}

    total_users = users.count()

    department_distribution = (
        users.values("department__name").annotate(count=Count("id")).order_by("-count")
    )

    departments = {
        d["department__name"] or "Unassigned": d["count"]
        for d in department_distribution
    }

    role_distribution = users.values("role").annotate(count=Count("id"))

    roles = {r["role"] or "unknown": r["count"] for r in role_distribution}

    joined_last_30 = users.filter(
        joining_date__date__gte=today - timedelta(days=30)
    ).count()

    joined_last_90 = users.filter(
        joining_date__date__gte=today - timedelta(days=90)
    ).count()

    joined_last_year = users.filter(
        joining_date__date__gte=today - timedelta(days=365)
    ).count()

    tenure_years = []
    for jd in users.exclude(joining_date__isnull=True).values_list(
        "joining_date", flat=True
    ):
        tenure_years.append((today - jd.date()).days / 365)

    avg_tenure = (
        round(sum(tenure_years) / len(tenure_years), 1) if tenure_years else None
    )

    birth_months = (
        users.exclude(birthdate__isnull=True)
        .annotate(month=ExtractMonth("birthdate"))
        .values("month")
        .annotate(count=Count("id"))
    )

    birth_month_distribution = {b["month"]: b["count"] for b in birth_months}

    upcoming_birthdays = users.filter(birthdate__month=today.month).count()

    avg_ctc = users.exclude(salary_ctc__isnull=True).aggregate(avg=Avg("salary_ctc"))[
        "avg"
    ]

    salary_bands = {
        "below_5L": users.filter(salary_ctc__lt=500000).count(),
        "5L_to_10L": users.filter(
            salary_ctc__gte=500000, salary_ctc__lt=1000000
        ).count(),
        "above_10L": users.filter(salary_ctc__gte=1000000).count(),
    }
    context = {
        "total_active_users": total_users,
        "role_distribution": roles,
        "department_distribution": departments,
        "joining_trends": {
            "last_30_days": joined_last_30,
            "last_90_days": joined_last_90,
            "last_1_year": joined_last_year,
            "average_tenure_years": avg_tenure,
        },
        "birth_patterns": {
            "birth_month_distribution": birth_month_distribution,
            "birthdays_this_month": upcoming_birthdays,
        },
        "salary_patterns": {
            "average_ctc": round(avg_ctc, 2) if avg_ctc else None,
            "salary_bands": salary_bands,
        },
    }
    print(f"==>> context: {context}")
    return context


def calculate_general_patterns():
    pass


def calculate_holiday_patterns():
    """Calutaing patterns or percentage of holidays here"""
    today = timezone.now().date()
    year_start = today.replace(month=1, day=1)
    year_end = today.replace(month=12, day=31)

    holidays = models.Holiday.objects.filter(
        date__range=(year_start, year_end)
    ).order_by("date")
    total_holidays = holidays.count()

    month_counts = (
        holidays.annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(count=Count("id"))
    )
    month_wise = {m["month"]: m["count"] for m in month_counts}

    weekday_map = {
        1: "Sunday",
        2: "Monday",
        3: "Tuesday",
        4: "Wednesday",
        5: "Thursday",
        6: "Friday",
        7: "Saturday",
    }
    weekday_counts = (
        holidays.annotate(day=ExtractWeekDay("date"))
        .values("day")
        .annotate(count=Count("id"))
    )
    weekday_distribution = {weekday_map[w["day"]]: w["count"] for w in weekday_counts}

    long_weekends = holidays.filter(date__week_day__in=[2, 6]).count()

    sandwich_risk = holidays.filter(date__week_day__in=[3, 4, 5]).count()

    holiday_dates = list(holidays.values_list("date", flat=True))

    clustered_periods = 0
    for i in range(len(holiday_dates) - 1):
        if (holiday_dates[i + 1] - holiday_dates[i]).days <= 3:
            clustered_periods += 1

    gaps = []
    for i in range(len(holiday_dates) - 1):
        gaps.append((holiday_dates[i + 1] - holiday_dates[i]).days)

    avg_gap = round(sum(gaps) / len(gaps), 1) if gaps else None

    avg_per_month = total_holidays / 12
    dense_months = [
        month for month, count in month_wise.items() if count > avg_per_month
    ]

    context = {
        "total_holidays": total_holidays,
        "month_wise_distribution": month_wise,
        "weekday_distribution": weekday_distribution,
        "long_weekend_opportunities": long_weekends,
        "sandwich_risk_holidays": sandwich_risk,
        "holiday_clusters": clustered_periods,
        "average_gap_between_holidays_days": avg_gap,
        "holiday_dense_months": dense_months,
    }
    print(f"==>> context: {context}")
    return context


def calculate_announcement_patterns():
    today = timezone.now().today()
    year_start = today.replace(month=1, day=1)
    year_end = today.replace(month=12, day=31)
    announcements = models.Announcement.objects.filter(
        date__range=(year_start, year_end)
    )
    announcement_count = announcements.count()

    month_counts = (
        announcements.annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(count=Count("id"))
    )
    month_wise = {m["month"]: m["count"] for m in month_counts}

    context = {
        "announcement_count": announcement_count,
        "annoucement_montly": month_wise,
    }
    print(f"==>> context: {context}")
    return context


def calculate_employee_patterns():
    pass
