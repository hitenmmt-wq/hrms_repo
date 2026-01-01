from django.db import models
from django.db.models import Q

from apps.base.models import BaseModel
from apps.superadmin.models import Users

# Create your models here.


class EmployeeAttendance(BaseModel):
    ATTENDANCE_TYPE = (
        ("present", "present"),
        ("unpaid_leave", "unpaid_leave"),
        ("paid_leave", "paid_leave"),
        ("half_day", "half_day"),
        ("incomplete_hours", "incomplete_hours"),
        ("pending", "pending"),
    )
    employee = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="attendance_employee"
    )
    day = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    break_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default="pending", choices=ATTENDANCE_TYPE)

    class Meta:
        indexes = [
            models.Index(fields=["employee", "day"]),
            models.Index(fields=["day", "status"]),
            models.Index(fields=["check_in"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "day"],
                condition=Q(is_deleted=False),
                name="unique_active_attendance_per_day",
            )
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.day} - {self.status}"


class AttendanceBreakLogs(BaseModel):
    attendance = models.ForeignKey(
        EmployeeAttendance,
        on_delete=models.CASCADE,
        related_name="attendance_break_logs",
    )
    pause_time = models.DateTimeField(null=True, blank=True)
    restart_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Break - {self.attendance.employee.email}"
