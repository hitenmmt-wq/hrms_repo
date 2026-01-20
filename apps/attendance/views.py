"""
Attendance views for employee time tracking and break management.

Handles check-in/check-out operations, break logging, daily attendance
records, and attendance management for the HRMS time tracking system.
"""

from django.utils import timezone
from rest_framework.decorators import action

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.attendance.serializers import (  # , IdleStatusSerializer
    AttendanceSerializer,
    BreakLogSerializer,
)
from apps.attendance.utils import check_in, check_out, pause_break, resume_break
from apps.base.permissions import IsAuthenticated
from apps.base.response import ApiResponse
from apps.base.viewset import BaseViewSet
from apps.superadmin.models import Users

# from rest_framework.views import APIView
# from rest_framework import status


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
        attendance = self.queryset.filter(
            employee=employee, day__lte=timezone.now().date()
        ).order_by("-day")
        return ApiResponse.success(
            "Particular Employee's Attendance list",
            AttendanceSerializer(attendance, many=True).data,
        )

    @action(detail=False, methods=["get"])
    def daily_logs(self, request):
        """Get daily break logs for the current user's attendance."""
        attendance = (
            self.get_queryset()
            .filter(employee=request.user, day=timezone.now().date())
            .select_related("employee")
            .first()
        )

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


# class IdleStatusView(APIView):
#     """API endpoint for receiving idle status updates from desktop application."""

#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         """Handle idle status updates and trigger auto-pause if needed."""
#         serializer = IdleStatusSerializer(data=request.data)

#         if not serializer.is_valid():
#             return ApiResponse.error("Invalid data", serializer.errors, status.HTTP_400_BAD_REQUEST)

#         data = serializer.validated_data
#         user = request.user

#         # Get today's attendance record
#         today_attendance = EmployeeAttendance.objects.filter(
#             employee=user,
#             day=timezone.now().date()
#         ).first()

#         if not today_attendance:
#             return ApiResponse.error("No attendance record found for today", status_code=status.HTTP_404_NOT_FOUND)

#         # Handle idle status
#         if data['is_idle']:
#             # Auto-pause work if user is idle and currently working
#             if today_attendance.track_current_status == 'ongoing':
#                 pause_break(today_attendance)
#                 return ApiResponse.success({
#                     "message": "Work auto-paused due to inactivity",
#                     "idle_duration": data['idle_duration'],
#                     "action": "paused"
#                 })


#         return ApiResponse.success({
#             "message": "Idle status received",
#             "current_status": today_attendance.track_current_status,
#             "action": "none"
#         })


# class IdleDetectorHealthView(APIView):
#     """Health check endpoint for idle detector connection status."""

#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """Check if idle detector is properly configured and connected."""
#         user = request.user
#         print("------------this function is called for detecting of application running ------------")

#         today_attendance = EmployeeAttendance.objects.filter(
#             employee=user,
#             day=timezone.now().date()
#         ).first()

#         return ApiResponse.success({
#             "status": "connected",
#             "employee_id": user.id,
#             "employee_name": f"{user.first_name} {user.last_name}",
#             "has_attendance_today": bool(today_attendance),
#             "current_status": today_attendance.track_current_status if today_attendance else None,
#             "timestamp": timezone.now().isoformat()
#         })
