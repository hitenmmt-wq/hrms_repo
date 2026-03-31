"""
Attendance views for employee time tracking and break management.

Handles check-in/check-out operations, break logging, daily attendance
records, and attendance management for the HRMS time tracking system.
"""

import calendar

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.attendance.custom_filters import EmployeeAttendanceFilter
from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.attendance.serializers import (  # , IdleStatusSerializer
    AttendanceSerializer,
    BreakLogSerializer,
)
from apps.attendance.utils import (
    check_in,
    check_out,
    get_weekend_days,
    pause_break,
    resume_break,
)
from apps.base import constants
from apps.base.pagination import CustomPageNumberPagination
from apps.base.permissions import IsAuthenticated
from apps.base.response import ApiResponse
from apps.base.viewset import BaseViewSet
from apps.superadmin.models import Holiday, Users


class AttendanceViewSet(BaseViewSet):
    """Attendance management ViewSet for employee time tracking operations."""

    queryset = EmployeeAttendance.objects.select_related(
        "employee__department", "employee__position"
    )
    pagination_class = CustomPageNumberPagination
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = EmployeeAttendanceFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
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
        page = self.paginate_queryset(attendance)
        if page is not None:
            serializer = AttendanceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AttendanceSerializer(attendance, many=True)
        return ApiResponse.success(
            "Particular Employee's Attendance list", serializer.data
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
        if not attendance or isinstance(attendance, str):
            return ApiResponse.error(attendance, status=400)
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

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def get_attendance_summary(self, request):
        context = {}
        attendance_id = request.query_params.get("attendance_id")
        attendance = EmployeeAttendance.objects.filter(id=attendance_id).first()
        break_logs = AttendanceBreakLogs.objects.filter(attendance=attendance)
        context["break_log"] = BreakLogSerializer(break_logs, many=True).data
        context["attendance_detail"] = AttendanceSerializer(attendance).data
        return ApiResponse.success("Attendance Summary", data=context)


class AttendanceCalenderViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_month = int(request.query_params.get("month"))
        current_year = int(request.query_params.get("year"))
        employee_id = int(request.query_params.get("employee_id"))
        if not employee_id:
            return ApiResponse.error("Employee ID is required", status=400)
        if not current_month and not current_year:
            return ApiResponse.error("Month and Year is required", status=400)

        employee = Users.objects.filter(id=employee_id).first()
        attendances = EmployeeAttendance.objects.filter(
            employee=employee, day__month=current_month, day__year=current_year
        ).order_by("day")
        attendance_month_wise = []
        total_work_hours = 0
        for attendance in attendances:
            attendance_month_wise.append(
                {
                    "date": attendance.day.strftime("%Y-%m-%d"),
                    "status": attendance.status,
                    "check_in": (attendance.check_in if attendance.check_in else None),
                    "check_out": (
                        attendance.check_out if attendance.check_out else None
                    ),
                    "work_hours": attendance.work_hours,
                    "break_hours": attendance.break_hours,
                }
            )
            total_work_hours = sum(attendance.work_hours for attendance in attendances)
        holidays = Holiday.objects.filter(
            date__month=current_month, date__year=current_year
        )

        for holiday in holidays:
            attendance_month_wise.append(
                {
                    "date": holiday.date.strftime("%Y-%m-%d"),
                    "status": "Holiday",
                    "name": holiday.name,
                }
            )

        weekend_days = get_weekend_days(current_month, current_year)
        for weekend_day in weekend_days:
            attendance_month_wise.append(
                {"date": weekend_day.strftime("%Y-%m-%d"), "status": "Weekend"}
            )
        attendance_month_wise.sort(key=lambda x: x["date"])
        working_days = calendar.monthrange(current_year, current_month)[1]
        official_working_days = working_days - (len(weekend_days) + holidays.count())
        official_working_hours = (
            official_working_days * constants.OFFICIAL_WORKING_HOURS
        )
        total_attendance = len(
            attendances.exclude(
                status__in=[
                    constants.PENDING,
                    constants.PAID_LEAVE,
                    constants.UNPAID_LEAVE,
                ]
            )
        )
        attendance_month_wise.append(
            {
                "official_working_days": official_working_days,
                "total_attendance": total_attendance,
                "official_working_hours": official_working_hours,
                "total_work_hours": total_work_hours,
                "total_holidays": holidays.count(),
                "total_weekends": len(weekend_days),
            }
        )
        return ApiResponse.success(
            "Attendance calender data fetched", data=attendance_month_wise
        )
