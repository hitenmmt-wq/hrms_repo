from rest_framework import serializers
from apps.superadmin import models
from apps.employee.models import LeaveBalance
from apps.attendance.models import EmployeeAttendance


#  ==================================== EMPLOYEE SERIALIZER ======================================================================


class EmployeeCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=models.Department.objects.all()
    )
    position = serializers.PrimaryKeyRelatedField(
        queryset=models.Position.objects.all()
    )

    class Meta:
        model = models.Users
        fields = [
            "first_name",
            "last_name",
            "email",
            "role",
            "department",
            "position",
            "employee_id",
            "password",
            "joining_date",
        ]
        depth = 1

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = models.Users(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmployeeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "department",
            "position",
            "employee_id",
            "joining_date",
            "is_active",
        ]
        depth = 1


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    department = serializers.PrimaryKeyRelatedField(
        queryset=models.Department.objects.all()
    )
    position = serializers.PrimaryKeyRelatedField(
        queryset=models.Position.objects.all()
    )

    class Meta:
        model = models.Users
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "role",
            "department",
            "position",
            "employee_id",
            "password",
            "joining_date",
        ]
        depth = 1

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


#  ==================================== LEAVE BALANCE SERIALIZER ======================================================================


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())

    class Meta:
        model = LeaveBalance
        fields = ["id", "employee", "year", "pl", "sl", "lop"]
        depth = 1


#  ==================================== APPLY LEAVE SERIALIZER ======================================================================


class ApplyLeaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Leave
        fields = [
            "id",
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "total_days",
            "reason",
            "status",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["employee"] = {
            "first_name": instance.employee.first_name,
            "last_name": instance.employee.last_name,
        }

        return representation


class ApplyLeaveCreateSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())
    # approved_by = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())

    class Meta:
        model = models.Leave
        fields = [
            "id",
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "total_days",
            "reason",
            "status",
        ]


#  ==================================== DASHBOARD SERIALIZER ======================================================================


class HolidayMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Holiday
        fields = ["id", "name", "date"]


class LeaveMiniSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)

    class Meta:
        model = models.Leave
        fields = [
            "id",
            "employee",
            "leave_type",
            "total_days",
            "status",
            "from_date",
            "to_date",
        ]
        depth = 1


class TodayAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendance
        fields = ["id", "day", "check_in", "check_out"]
        depth = 1
