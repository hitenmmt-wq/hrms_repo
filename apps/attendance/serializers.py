"""
Attendance serializers for time tracking data validation and transformation.

Handles serialization for employee attendance records, break logs,
and time tracking functionality for the HRMS attendance system.
"""

from rest_framework import serializers

from apps.attendance.models import AttendanceBreakLogs, EmployeeAttendance
from apps.employee.serializers import EmployeeListSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for employee attendance records with employee details and status tracking."""

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
