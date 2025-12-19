from rest_framework import serializers

from apps.attendance.models import EmployeeAttendance
from apps.employee.models import LeaveBalance, PaySlip
from apps.employee.utils import calculate_leave_deduction, weekdays_count
from apps.superadmin import models

#   ======= EMPLOYEE SERIALIZER   ============


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
            "birthdate",
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


#   ======= LEAVE BALANCE SERIALIZER   ============


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())

    class Meta:
        model = LeaveBalance
        fields = ["id", "employee", "year", "pl", "sl", "lop"]
        depth = 1


#   ======= APPLY LEAVE SERIALIZER   ============


class ApplyLeaveSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)

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


class ApplyLeaveCreateSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())

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


#   ======= DASHBOARD SERIALIZER   ============


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


# ===================================


class PaySlipCreateSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())

    class Meta:
        model = PaySlip
        fields = [
            "id",
            "employee",
            "start_date",
            "end_date",
            "month",
            "days",
            "basic_salary",
            "hr_allowance",
            "special_allowance",
            "tax_deductions",
            "total_earnings",
            "other_deductions",
            "leave_deductions",
            "total_deductions",
            "net_salary",
        ]

    def create(self, validated_data):
        employee = validated_data["employee"]
        start_date = validated_data["start_date"]
        end_date = validated_data["end_date"]

        validated_data["month"] = end_date.strftime("%B")
        validated_data["days"] = weekdays_count(start_date, end_date)

        leave_deductions = calculate_leave_deduction(
            employee,
            start_date,
            end_date,
            validated_data["basic_salary"],
            validated_data["hr_allowance"],
            validated_data["special_allowance"],
        )

        validated_data["leave_deductions"] = leave_deductions

        total_earnings = (
            validated_data["basic_salary"]
            + validated_data["hr_allowance"]
            + validated_data["special_allowance"]
        )

        total_deductions = (
            validated_data["tax_deductions"]
            + leave_deductions
            + validated_data["other_deductions"]
        )

        validated_data["total_earnings"] = total_earnings
        validated_data["total_deductions"] = total_deductions
        validated_data["net_salary"] = total_earnings - total_deductions

        return super().create(validated_data)

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        start_date = validated_data.get("start_date", instance.start_date)
        end_date = validated_data.get("end_date", instance.end_date)

        instance.month = end_date.strftime("%B")
        instance.days = weekdays_count(start_date, end_date)

        total_earnings = (
            validated_data.get("basic_salary", instance.basic_salary)
            + validated_data.get("hr_allowance", instance.hr_allowance)
            + validated_data.get("special_allowance", instance.special_allowance)
        )

        total_deductions = (
            validated_data.get("tax_deductions", instance.tax_deductions)
            + validated_data.get("leave_deductions", instance.leave_deductions)
            + validated_data.get("other_deductions", instance.other_deductions)
        )

        instance.total_earnings = total_earnings
        instance.total_deductions = total_deductions
        instance.net_salary = total_earnings - total_deductions

        instance.save()
        return instance


class PaySlipSerializer(serializers.ModelSerializer):
    employee = EmployeeListSerializer(read_only=True)

    class Meta:
        model = PaySlip
        fields = [
            "id",
            "employee",
            "start_date",
            "end_date",
            "month",
            "days",
            "basic_salary",
            "hr_allowance",
            "special_allowance",
            "total_earnings",
            "tax_deductions",
            "other_deductions",
            "leave_deductions",
            "total_deductions",
            "net_salary",
        ]
