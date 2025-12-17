from datetime import date, timedelta
from typing import Tuple

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.superadmin.models import Attendance, Leave, LeaveBalance

User = get_user_model()


def daterange(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def get_or_create_balance(employee: User, year: int | None = None) -> LeaveBalance:
    year = year or timezone.now().year
    balance, _ = LeaveBalance.objects.get_or_create(employee=employee, year=year)
    return balance


@transaction.atomic
def apply_leave(
    employee: User, leave_type: str, start_date: date, end_date: date, reason: str = ""
) -> Leave:
    if end_date < start_date:
        raise ValueError("end_date must be >= start_date")

    total_days = (end_date - start_date).days + 1

    # check overlapping approved leaves
    overlapping = Leave.objects.filter(
        employee=employee, status=Leave.LEAVE_STATUS_APPROVED
    ).filter(Q(start_date__lte=end_date) & Q(end_date__gte=start_date))
    if overlapping.exists():
        raise ValueError("You have already approved leave in the selected date range.")

    leave = Leave.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        reason=reason,
    )
    # Optionally mark attendance as "pending_leave" for these dates
    _mark_attendance_pending_for_leave(employee, start_date, end_date)
    return leave


def _mark_attendance_pending_for_leave(
    employee: User, start_date: date, end_date: date
) -> None:
    """Mark attendance rows as pending_leave to avoid auto-absent logic clashing."""
    for day in daterange(start_date, end_date):
        Attendance.objects.update_or_create(
            employee=employee,
            date=day,
            defaults={
                "status": "pending_leave",
                "check_in": None,
                "check_out": None,
                "work_hours": 0,
            },
        )


@transaction.atomic
def approve_leave(approver: User, leave_id: int) -> Tuple[Leave, dict]:
    leave = (
        Leave.objects.select_for_update().select_related("employee").get(id=leave_id)
    )

    if leave.status != Leave.LEAVE_STATUS_PENDING:
        raise ValueError("Only pending leaves can be approved.")

    balance = get_or_create_balance(leave.employee, leave.start_date.year)

    lop_added = 0

    # Deduct balances
    if leave.leave_type == Leave.LEAVE_TYPE_PL:
        available = balance.pl
        if available >= leave.total_days:
            balance.pl = available - leave.total_days
            lop_added = 0
        else:
            lop_added = leave.total_days - available
            balance.pl = 0
            balance.lop += lop_added

    elif leave.leave_type == Leave.LEAVE_TYPE_SL:
        available = balance.sl
        if available >= leave.total_days:
            balance.sl = available - leave.total_days
            lop_added = 0
        else:
            lop_added = leave.total_days - available
            balance.sl = 0
            balance.lop += lop_added

    # persist balance
    balance.save(update_fields=["pl", "sl", "lop"])

    # update leave
    leave.status = Leave.LEAVE_STATUS_APPROVED
    leave.approved_at = timezone.now()
    leave.approved_by = approver
    leave.save(update_fields=["status", "approved_at", "approved_by"])

    # update attendance for those dates
    update_attendance_for_leave(leave)

    return leave, {"lop_added": lop_added}


def update_attendance_for_leave(leave: Leave) -> None:
    """Set attendance rows for each leave date to status='leave' and work_hours=0."""
    for day in daterange(leave.start_date, leave.end_date):
        Attendance.objects.update_or_create(
            employee=leave.employee,
            date=day,
            defaults={
                "status": "leave",
                "check_in": None,
                "check_out": None,
                "work_hours": 0,
            },
        )


def auto_mark_absent_and_lop(process_date: date) -> None:

    employees = User.objects.filter(is_active=True).select_related("leave_balance")
    for emp in employees:
        # skip if approved leave exists for date
        has_leave = Leave.objects.filter(
            employee=emp,
            status=Leave.LEAVE_STATUS_APPROVED,
            start_date__lte=process_date,
            end_date__gte=process_date,
        ).exists()
        if has_leave:
            continue

        attendance, created = Attendance.objects.get_or_create(
            employee=emp, date=process_date
        )
        if attendance.status in ("present", "leave"):
            continue

        # if no check_in and not pending_leave
        if attendance.check_in is None and attendance.status != "pending_leave":
            attendance.status = "absent"
            attendance.work_hours = 0
            attendance.save(update_fields=["status", "work_hours"])

            # increment LOP in leave balance
            balance = get_or_create_balance(emp, process_date.year)
            balance.lop += 1
            balance.save(update_fields=["lop"])
