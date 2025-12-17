# from rest_framework import serializers
# from apps.attendanceapp import models


# class AttendanceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Attendance
#         fields = '__all__'
#         depth = 1


# class AttendanceListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Attendance
#         fields = '__all__'
#         depth = 1


from rest_framework import serializers
from apps.attendance.models import EmployeeAttendance, AttendanceBreakLogs


class AttendanceSerializer(serializers.ModelSerializer):
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
