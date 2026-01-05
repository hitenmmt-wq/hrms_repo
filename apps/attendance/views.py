"""
Attendance views for employee time tracking and break management.

Handles check-in/check-out operations, break logging, daily attendance
records, and attendance management for the HRMS time tracking system.
"""

from django.utils import timezone
from rest_framework.decorators import action

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.attendance.serializers import AttendanceSerializer, BreakLogSerializer
from apps.attendance.utils import check_in, check_out, pause_break, resume_break
from apps.base.permissions import IsAuthenticated
from apps.base.response import ApiResponse
from apps.base.viewset import BaseViewSet
from apps.superadmin.models import Users


class AttendanceViewSet(BaseViewSet):
    """Attendance management ViewSet for employee time tracking operations."""

    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = EmployeeAttendance.objects.select_related(
        "employee__department", "employee__position"
    )
    order_by = ["-day"]

    def destroy(self, request, *args, **kwargs):
        """Delete attendance record with success response."""
        instance = self.get_object()
        instance.delete()

        return ApiResponse.success(
            {
                "message": "Attendance deleted successfully",
                "status": "HTTP_200_OK",
            }
        )

    @action(detail=True, methods=["get"])
    def particular_employee(self, request, pk=None):
        """Get attendance records for a specific employee."""
        employee = (
            Users.objects.select_related("department", "position").filter(id=pk).first()
        )
        attendance = self.queryset.filter(employee=employee).order_by("-day")
        return ApiResponse.success(
            "Particular Employee's Attendance list",
            AttendanceSerializer(attendance, many=True).data,
        )

    @action(detail=False, methods=["get"])
    def daily_logs(self, request):
        """Get daily break logs for the current user's attendance."""
        attendance = (
            self.get_queryset()
            .filter(day=timezone.now().date())
            .select_related("employee")
            .first()
        )
        print(f"==>> attendance: {attendance.id}")

        logs = (
            AttendanceBreakLogs.objects.filter(attendance=attendance)
            .select_related("attendance__employee")
            .order_by("-id")
        )
        print(f"==>> logs: {logs}")

        return ApiResponse.success(
            "Daily logs list", BreakLogSerializer(logs, many=True).data
        )

    @action(detail=False, methods=["post"])
    def check_in(self, request):
        """Handle employee check-in for daily attendance."""
        attendance = check_in(request.user)
        return ApiResponse.success(
            "Attendance Created Successfully", AttendanceSerializer(attendance).data
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause work session and start break time logging."""
        pause_break(self.get_object())
        return ApiResponse.success("Work paused")

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        """Resume work session and end break time logging."""
        resume_break(self.get_object())
        return ApiResponse.success("Work resumed")

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        """Handle employee check-out and calculate total work hours."""
        attendance = check_out(self.get_object())
        return ApiResponse.success(
            "Logged out successfully", AttendanceSerializer(attendance).data
        )
