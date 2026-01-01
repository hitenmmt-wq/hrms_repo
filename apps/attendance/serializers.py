from rest_framework import serializers

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.employee.serializers import EmployeeListSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer()
    track_current_status = serializers.CharField(read_only=True)

    class Meta:
        model = EmployeeAttendance
        fields = "__all__"
        depth = 1
        read_only_fields = (
            "check_in",
            "check_out",
            "work_hours",
            "break_hours",
            "status",
        )


class BreakLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceBreakLogs
        fields = "__all__"
        depth = 1
