from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.superadmin.models import Users


def _calculate_break_hours(attendance: EmployeeAttendance) -> Decimal:
    print("-------calculate break hours called-----------")
    total = Decimal("0.0")

    for br in attendance.attendance_break_logs.all():
        if br.restart_time:
            diff = br.restart_time - br.pause_time
            total += Decimal(diff.total_seconds() / 3600)

    return total


def _calculate_status(work_hours: Decimal) -> str:
    if work_hours >= 8:
        return "present"
    if work_hours >= 4:
        return "half_day"
    if work_hours > 0:
        return "incomplete_hours"
    return "unpaid_leave"


@transaction.atomic
def check_in(employee: Users) -> EmployeeAttendance:
    today = timezone.localdate()

    attendance, created = EmployeeAttendance.objects.get_or_create(
        employee=employee, day=today, defaults={"check_in": timezone.now()}
    )

    if not created and attendance.check_in:
        raise ValueError("Already checked in")

    attendance.check_in = timezone.now()
    attendance.save(update_fields=["check_in"])
    update_attendance_hours(attendance)

    return attendance


@transaction.atomic
def pause_break(attendance: EmployeeAttendance) -> AttendanceBreakLogs:
    if AttendanceBreakLogs.objects.filter(
        attendance=attendance, restart_time__isnull=True
    ).exists():
        raise ValueError("Break already paused")
    update_attendance_hours(attendance)

    return AttendanceBreakLogs.objects.create(
        attendance=attendance, pause_time=timezone.now()
    )


@transaction.atomic
def resume_break(attendance: EmployeeAttendance) -> AttendanceBreakLogs:
    br = AttendanceBreakLogs.objects.filter(
        attendance=attendance, restart_time__isnull=True
    ).first()

    if not br:
        raise ValueError("No active break found")

    br.restart_time = timezone.now()
    br.save(update_fields=["restart_time"])
    update_attendance_hours(attendance)
    return br


@transaction.atomic
def update_attendance_hours(attendance: EmployeeAttendance) -> EmployeeAttendance:
    if attendance.check_out:
        total_hours = Decimal(
            (attendance.check_out - attendance.check_in).total_seconds() / 3600
        )
    else:
        total_hours = Decimal(
            (timezone.now() - attendance.check_in).total_seconds() / 3600
        )
    break_hours = _calculate_break_hours(attendance)
    work_hours = max(Decimal("0.0"), total_hours - break_hours)

    attendance.work_hours = work_hours - break_hours
    attendance.break_hours = break_hours
    attendance.status = _calculate_status(work_hours)

    attendance.save(update_fields=["work_hours", "break_hours", "status"])
    return attendance


@transaction.atomic
def check_out(attendance: EmployeeAttendance) -> EmployeeAttendance:
    if not attendance.check_in:
        raise ValueError("Check-in missing")

    attendance.check_out = timezone.now()

    total_hours = Decimal(
        (attendance.check_out - attendance.check_in).total_seconds() / 3600
    )

    break_hours = _calculate_break_hours(attendance)
    work_hours = max(Decimal("0.0"), total_hours - break_hours)

    attendance.work_hours = work_hours - break_hours
    attendance.break_hours = break_hours
    attendance.status = _calculate_status(work_hours)

    attendance.save(update_fields=["check_out", "work_hours", "break_hours", "status"])

    return attendance
