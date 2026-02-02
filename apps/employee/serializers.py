"""
Employee serializers for data validation and transformation.

Handles serialization for employee management, leave applications,
leave balance tracking, payslip generation, and dashboard data
for the HRMS employee module.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.attendance.models import EmployeeAttendance
from apps.employee.models import LeaveBalance, PaySlip
from apps.employee.utils import calculate_leave_deduction, weekdays_count
from apps.superadmin import models
from apps.superadmin.tasks import send_email_task


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new employees with password hashing and email notification."""

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
            "birthdate",
            "salary_ctc",
        ]
        depth = 1

    def create(self, validated_data):
        """Create employee with hashed password and send welcome email."""
        password = validated_data.pop("password")
        user = models.Users(**validated_data)
        user.set_password(password)
        user.save()
        try:
            LeaveBalance.objects.get(employee=user, year=timezone.now().year)
            print("Leave balance exists")
        except LeaveBalance.DoesNotExist:
            LeaveBalance.objects.create(
                employee=user,
                year=timezone.now().year,
            )
        try:
            send_email_task(
                subject="Welcome to HRMS",
                to_email=user.email,
                text_body=f"You have been added as an {user.role} to HRMS",
                html_body=None,
                pdf_bytes=None,
                filename=None,
            )
            print("done success.......")
        except Exception as e:
            print("error.......", e)

        return user


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for employee list display with department and position details."""

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
            "salary_ctc",
        ]
        depth = 1


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee information with optional password change."""

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
            "salary_ctc",
        ]
        depth = 1

    def update(self, instance, validated_data):
        """Update employee with optional password hashing."""
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for employee leave balance management and tracking."""

    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())

    class Meta:
        model = LeaveBalance
        fields = [
            "id",
            "employee",
            "year",
            "pl",
            "sl",
            "lop",
            "used_pl",
            "used_sl",
            "used_lop",
            "remaining_pl",
            "remaining_sl",
            "remaining_lop",
        ]
        depth = 1


class ApplyLeaveSerializer(serializers.ModelSerializer):
    """Serializer for displaying leave applications with employee details."""

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
            "day_part",
            "reason",
            "is_sandwich_applied",
            "status",
        ]
        depth = 1


class ApplyLeaveCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new leave applications."""

    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())
    leave_type = serializers.PrimaryKeyRelatedField(
        queryset=models.LeaveType.objects.all()
    )

    class Meta:
        model = models.Leave
        fields = [
            "id",
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "day_part",
            "total_days",
            "reason",
            "is_sandwich_applied",
            "status",
        ]


class HolidayMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for holiday information in dashboard displays."""

    class Meta:
        model = models.Holiday
        fields = ["id", "name", "date"]


class LeaveMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for leave information in dashboard displays."""

    employee = EmployeeListSerializer(read_only=True)
    leave_type = serializers.StringRelatedField()

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


class AnnouncementMiniSerializer(serializers.ModelSerializer):
    """Minimal serializer for announcement information in dashboard displays."""

    class Meta:
        model = models.Announcement
        fields = ["id", "title", "date", "description", "created_at"]
        depth = 1


class TodayAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for today's attendance information in employee dashboard."""

    class Meta:
        model = EmployeeAttendance
        fields = ["id", "day", "check_in", "check_out"]
        depth = 1


class PaySlipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payslips with automatic calculations."""

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
        """Create payslip with automatic calculations for earnings, deductions, and net salary."""
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
        """Update payslip with recalculated earnings, deductions, and net salary."""
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
    """Serializer for displaying payslip information with employee details."""

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
