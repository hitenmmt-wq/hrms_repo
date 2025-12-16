from rest_framework import viewsets, status
from rest_framework.decorators import action
from apps.base.response import ApiResponse
from apps.attendance.models import EmployeeAttendance, AttendanceBreakLogs
from apps.attendance.serializers import AttendanceSerializer, BreakLogSerializer
from apps.attendance.utils import (
    check_in, pause_break, resume_break, check_out
)
from apps.base.permissions import IsEmployee, IsAuthenticated
from django.utils import timezone



class AttendanceViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        attendance = EmployeeAttendance.objects.filter(employee=request.user)
        return ApiResponse.success(
            "Attendance list",
            AttendanceSerializer(attendance, many=True).data
        )
        
    @action(detail=False, methods=["get"])
    def daily_logs(self, request):
        attendance = EmployeeAttendance.objects.filter(employee=request.user,day=timezone.now().date()).first()
        daily_data = AttendanceBreakLogs.objects.filter(attendance=attendance).order_by("-id")
        return ApiResponse.success(
            "Daily logs List",
            BreakLogSerializer(daily_data, many=True).data
        )

    @action(detail=False, methods=["post"])
    def delete(self, request, pk=None):
        print(f"==>> pk: {pk}")
        EmployeeAttendance.objects.filter(id=pk).delete()
        return ApiResponse.success("Attendance deleted successfully")
        
    @action(detail=False, methods=["post"])
    def check_in(self, request):
        attendance = check_in(request.user)
        return ApiResponse.success(
            "Logged in successfully",
            AttendanceSerializer(attendance).data
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        attendance = EmployeeAttendance.objects.filter(id=pk, employee=request.user).first()
        pause_break(attendance)
        return ApiResponse.success("Work paused")

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        attendance = EmployeeAttendance.objects.filter(id=pk, employee=request.user).first()
        resume_break(attendance)
        return ApiResponse.success("Work resumed")

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        attendance = EmployeeAttendance.objects.filter(id=pk, employee=request.user).first()
        attendance = check_out(attendance)
        return ApiResponse.success(
            "Logged out successfully",
            AttendanceSerializer(attendance).data
        )
