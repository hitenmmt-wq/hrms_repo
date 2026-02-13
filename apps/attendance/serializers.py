"""
Attendance serializers for time tracking data validation and transformation.

Handles serialization for employee attendance records, break logs,
and time tracking functionality for the HRMS attendance system.
"""

from rest_framework import serializers

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.attendance.utils import decimal_hours_to_hm
from apps.employee.serializers import EmployeeListSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for employee attendance records with employee details and status tracking."""

    employee = EmployeeListSerializer()
    get_current_time = serializers.CharField(read_only=True)
    track_current_status = serializers.CharField(read_only=True)
    work_hours = serializers.SerializerMethodField()
    break_hours = serializers.SerializerMethodField()

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

    def get_work_hours(self, obj):
        return decimal_hours_to_hm(obj.work_hours)

    def get_break_hours(self, obj):
        return decimal_hours_to_hm(obj.break_hours)


class BreakLogSerializer(serializers.ModelSerializer):
    """Serializer for attendance break logs with pause and resume timestamps."""

    class Meta:
        model = AttendanceBreakLogs
        fields = "__all__"
        depth = 1


# class IdleStatusSerializer(serializers.Serializer):
#     """Serializer for idle status updates from desktop application."""

#     is_idle = serializers.BooleanField()
#     timestamp = serializers.DateTimeField()
#     idle_duration = serializers.FloatField(min_value=0)
