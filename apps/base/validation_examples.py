"""
Example usage of base validators in serializers.
This file demonstrates how to integrate the validation utilities into your existing serializers.
"""

from rest_framework import serializers

from apps.base.validators import (
    AttendanceValidator,
    BaseValidator,
    EmployeeValidator,
    LeaveValidator,
    PayrollValidator,
    ValidatedEmailField,
    ValidatedNameField,
    ValidatedPasswordField,
    ValidatedPhoneField,
    validate_department_exists,
    validate_position_exists,
    validate_unique_email,
)


class ExampleUserSerializer(serializers.ModelSerializer):
    """Example of using validators in user serializer."""

    # Using custom validated fields
    email = ValidatedEmailField()
    phone = ValidatedPhoneField(required=False, allow_blank=True)
    first_name = ValidatedNameField(field_name="First name")
    last_name = ValidatedNameField(field_name="Last name")
    password = ValidatedPasswordField(write_only=True)

    class Meta:
        model = None  # Replace with your User model
        fields = [
            "email",
            "phone",
            "first_name",
            "last_name",
            "password",
            "department",
            "position",
        ]

    def validate_email(self, value):
        """Additional email validation for uniqueness."""
        exclude_id = self.instance.id if self.instance else None
        return validate_unique_email(value, exclude_id)

    def validate_department(self, value):
        """Validate department exists."""
        return validate_department_exists(value.id if value else None)

    def validate_position(self, value):
        """Validate position exists."""
        return validate_position_exists(value.id if value else None)

    def validate_birth_date(self, value):
        """Validate birth date using employee validator."""
        return EmployeeValidator.validate_birth_date(value)


class ExampleLeaveSerializer(serializers.ModelSerializer):
    """Example of using validators in leave serializer."""

    class Meta:
        model = None  # Replace with your Leave model
        fields = [
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "total_days",
            "reason",
        ]

    def validate(self, attrs):
        """Cross-field validation for leave dates."""
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")
        total_days = attrs.get("total_days")

        # Validate date range
        LeaveValidator.validate_leave_dates(from_date, to_date)

        # Validate total days
        if total_days:
            LeaveValidator.validate_leave_days(total_days)

        return attrs


class ExampleAttendanceSerializer(serializers.ModelSerializer):
    """Example of using validators in attendance serializer."""

    class Meta:
        model = None  # Replace with your Attendance model
        fields = ["employee", "day", "check_in", "check_out", "total_hours"]

    def validate_check_in(self, value):
        """Validate check-in time."""
        return AttendanceValidator.validate_check_in_time(value)

    def validate(self, attrs):
        """Cross-field validation for check-in/check-out times."""
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")

        if check_in and check_out:
            AttendanceValidator.validate_check_out_time(check_in, check_out)

        return attrs


class ExamplePayrollSerializer(serializers.ModelSerializer):
    """Example of using validators in payroll serializer."""

    class Meta:
        model = None  # Replace with your Payroll model
        fields = ["employee", "month", "year", "basic_salary", "total_salary"]

    def validate_basic_salary(self, value):
        """Validate salary amount."""
        return PayrollValidator.validate_salary_amount(value)

    def validate_total_salary(self, value):
        """Validate total salary amount."""
        return PayrollValidator.validate_salary_amount(value)

    def validate(self, attrs):
        """Cross-field validation for payroll."""
        month = attrs.get("month")
        year = attrs.get("year")

        if month and year:
            PayrollValidator.validate_payroll_month_year(month, year)

        return attrs


# Example of using validators in views
class ExampleViewValidation:
    """Example of using validators directly in views."""

    def validate_password_change(self, old_password, new_password, confirm_password):
        """Example password change validation."""
        # Validate new password strength
        BaseValidator.validate_password(new_password)

        # Check if passwords match
        if new_password != confirm_password:
            raise serializers.ValidationError("New passwords do not match.")

        return new_password

    def validate_file_upload(self, file):
        """Example file upload validation."""
        # Validate file size (5MB max)
        BaseValidator.validate_file_size(file, max_size_mb=5)

        # Validate file extension for images
        allowed_extensions = ["jpg", "jpeg", "png", "gif"]
        BaseValidator.validate_file_extension(file, allowed_extensions)

        return file

    def validate_date_range_filter(self, start_date, end_date):
        """Example date range validation for filtering."""
        BaseValidator.validate_date_range(start_date, end_date, "Filter date")
        return start_date, end_date


# Custom validation mixins for reusable validation logic
class EmailValidationMixin:
    """Mixin for email validation in serializers."""

    def validate_email(self, value):
        exclude_id = self.instance.id if self.instance else None
        return validate_unique_email(value, exclude_id)


class DateRangeValidationMixin:
    """Mixin for date range validation in serializers."""

    def validate_date_range(self, from_date, to_date):
        return BaseValidator.validate_date_range(from_date, to_date)


class FileUploadValidationMixin:
    """Mixin for file upload validation in serializers."""

    def validate_profile_image(self, value):
        if value:
            BaseValidator.validate_file_size(value, max_size_mb=2)
            BaseValidator.validate_file_extension(value, ["jpg", "jpeg", "png"])
        return value

    def validate_document(self, value):
        if value:
            BaseValidator.validate_file_size(value, max_size_mb=10)
            BaseValidator.validate_file_extension(value, ["pdf", "doc", "docx"])
        return value
