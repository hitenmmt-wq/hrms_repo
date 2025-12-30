from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.attendance.serializers import AttendanceSerializer, BreakLogSerializer
from apps.attendance.utils import check_in, check_out, pause_break, resume_break
from apps.base.permissions import IsAuthenticated
from apps.base.response import ApiResponse
from apps.superadmin.models import Users


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = EmployeeAttendance.objects.all()
    order_by = ["-day"]

    def destroy(self, request, *args, **kwargs):
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
        employee = Users.objects.filter(id=pk).first()
        attendance = self.queryset.filter(employee=employee).order_by("-day")
        return ApiResponse.success(
            "Particular Employee's Attendance list",
            AttendanceSerializer(attendance, many=True).data,
        )

    @action(detail=False, methods=["get"])
    def daily_logs(self, request):
        attendance = self.get_queryset().filter(day=timezone.now().date()).first()

        logs = AttendanceBreakLogs.objects.filter(attendance=attendance).order_by("-id")

        return ApiResponse.success(
            "Daily logs list", BreakLogSerializer(logs, many=True).data
        )

    @action(detail=False, methods=["post"])
    def check_in(self, request):
        attendance = check_in(request.user)
        return ApiResponse.success(
            "Attendance Created Successfully", AttendanceSerializer(attendance).data
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        pause_break(self.get_object())
        return ApiResponse.success("Work paused")

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        resume_break(self.get_object())
        return ApiResponse.success("Work resumed")

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        attendance = check_out(self.get_object())
        return ApiResponse.success(
            "Logged out successfully", AttendanceSerializer(attendance).data
        )
