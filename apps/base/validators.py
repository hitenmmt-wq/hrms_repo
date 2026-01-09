"""
Base validation utilities for HRMS project.
Provides reusable validation functions and classes for common validation needs.
"""

import re
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.utils import timezone
from rest_framework import serializers


class BaseValidator:
    """Base validation class with common validation methods."""

    @staticmethod
    def validate_email(email):
        """Validate email format."""
        if not email:
            raise ValidationError("Email is required.")
        try:
            django_validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")
        return email.lower().strip()

    @staticmethod
    def validate_phone(phone):
        """Validate phone number format."""
        if not phone:
            return phone

        # Remove spaces and special characters
        cleaned_phone = re.sub(r"[^\d+]", "", phone)

        # Check if phone number is valid (10 digits, optional + prefix)
        if not re.match(r"^\+?[1-9]\d{9}$", cleaned_phone):
            raise ValidationError("Enter a valid phone number (10 digits).")

        return cleaned_phone

    @staticmethod
    def validate_password(password):
        """Validate password strength."""
        if not password:
            raise ValidationError("Password is required.")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", password):
            raise ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit.")

        return password

    @staticmethod
    def validate_name(name, field_name="Name"):
        """Validate name fields."""
        if not name:
            raise ValidationError(f"{field_name} is required.")

        name = name.strip()
        if len(name) < 2:
            raise ValidationError(f"{field_name} must be at least 2 characters long.")

        if len(name) > 50:
            raise ValidationError(f"{field_name} must not exceed 50 characters.")

        if not re.match(r"^[a-zA-Z\s\-\'\.]+$", name):
            raise ValidationError(
                f"{field_name} can only contain letters, spaces, hyphens, apostrophes, and periods."
            )

        return name

    @staticmethod
    def validate_date_range(from_date, to_date, field_prefix="Date"):
        """Validate date range."""
        if from_date and to_date:
            if from_date > to_date:
                raise ValidationError(
                    f"{field_prefix} range is invalid. Start date cannot be after end date."
                )
        return from_date, to_date

    @staticmethod
    def validate_future_date(date_value, field_name="Date"):
        """Validate that date is not in the past."""
        if date_value and date_value < timezone.now().date():
            raise ValidationError(f"{field_name} cannot be in the past.")
        return date_value

    @staticmethod
    def validate_past_date(date_value, field_name="Date"):
        """Validate that date is not in the future."""
        if date_value and date_value > timezone.now().date():
            raise ValidationError(f"{field_name} cannot be in the future.")
        return date_value

    @staticmethod
    def validate_file_size(file, max_size_mb=5):
        """Validate file size."""
        if file and file.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"File size cannot exceed {max_size_mb}MB.")
        return file

    @staticmethod
    def validate_file_extension(file, allowed_extensions):
        """Validate file extension."""
        if file:
            ext = file.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
                )
        return file


class EmployeeValidator(BaseValidator):
    """Employee-specific validation methods."""

    @staticmethod
    def validate_employee_id(employee_id):
        """Validate employee ID format."""
        if not employee_id:
            raise ValidationError("Employee ID is required.")

        if not re.match(r"^EMP\d{4,6}$", employee_id):
            raise ValidationError(
                "Employee ID must be in format EMP followed by 4-6 digits (e.g., EMP1234)."
            )

        return employee_id

    @staticmethod
    def validate_joining_date(joining_date):
        """Validate employee joining date."""
        if not joining_date:
            raise ValidationError("Joining date is required.")

        # Cannot be more than 50 years in the past
        min_date = timezone.now().date() - timedelta(days=365 * 50)
        if joining_date < min_date:
            raise ValidationError("Joining date cannot be more than 50 years ago.")

        # Cannot be more than 1 year in the future
        max_date = timezone.now().date() + timedelta(days=365)
        if joining_date > max_date:
            raise ValidationError(
                "Joining date cannot be more than 1 year in the future."
            )

        return joining_date

    @staticmethod
    def validate_birth_date(birth_date):
        """Validate employee birth date."""
        if not birth_date:
            return birth_date

        today = timezone.now().date()
        age = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )

        if age < 18:
            raise ValidationError("Employee must be at least 18 years old.")

        if age > 100:
            raise ValidationError("Employee won't be as productive as required.")

        return birth_date


class LeaveValidator(BaseValidator):
    """Leave management validation methods."""

    @staticmethod
    def validate_leave_dates(from_date, to_date):
        """Validate leave date range."""
        if not from_date:
            raise ValidationError("Leave start date is required.")

        if to_date and from_date > to_date:
            raise ValidationError("Leave end date cannot be before start date.")

        # Cannot apply for leave more than 1 year in advance
        max_future_date = timezone.now().date() + timedelta(days=365)
        if from_date > max_future_date:
            raise ValidationError("Cannot apply for leave more than 1 year in advance.")

        return from_date, to_date

    @staticmethod
    def validate_leave_days(total_days):
        """Validate leave duration."""
        if total_days <= 0:
            raise ValidationError("Leave duration must be at least 1 day.")

        if total_days > 90:
            raise ValidationError("Leave duration cannot exceed 90 days.")

        return total_days


class AttendanceValidator(BaseValidator):
    """Attendance validation methods."""

    @staticmethod
    def validate_check_in_time(check_in_time):
        """Validate check-in time."""
        if not check_in_time:
            raise ValidationError("Check-in time is required.")

        # Cannot check in more than 24 hours ago or in the future
        now = timezone.now()
        if check_in_time > now:
            raise ValidationError("Check-in time cannot be in the future.")

        if check_in_time < now - timedelta(hours=24):
            raise ValidationError("Cannot check in for more than 24 hours ago.")

        return check_in_time

    @staticmethod
    def validate_check_out_time(check_in_time, check_out_time):
        """Validate check-out time against check-in time."""
        if not check_out_time:
            return check_out_time

        if check_out_time <= check_in_time:
            raise ValidationError("Check-out time must be after check-in time.")

        # Maximum work day is 24 hours
        if check_out_time > check_in_time + timedelta(hours=24):
            raise ValidationError("Work duration cannot exceed 24 hours.")

        return check_out_time


class PayrollValidator(BaseValidator):
    """Payroll validation methods."""

    @staticmethod
    def validate_salary_amount(amount):
        """Validate salary amount."""
        return BaseValidator.validate_decimal_amount(
            amount,
            min_value=0,
            max_value=Decimal("10000000"),  # 1 crore max
            field_name="Salary",
        )

    @staticmethod
    def validate_payroll_month_year(month, year):
        """Validate payroll month and year."""
        if not month or not year:
            raise ValidationError("Month and year are required.")

        if month < 1 or month > 12:
            raise ValidationError("Month must be between 1 and 12.")

        current_year = timezone.now().year
        if year < current_year - 10 or year > current_year + 1:
            raise ValidationError(
                f"Year must be between {current_year - 10} and {current_year + 1}."
            )

        return month, year


# Serializer field validators
class ValidatedEmailField(serializers.EmailField):
    """Custom email field with enhanced validation."""

    def to_internal_value(self, data):
        return BaseValidator.validate_email(data)


class ValidatedPhoneField(serializers.CharField):
    """Custom phone field with validation."""

    def to_internal_value(self, data):
        return BaseValidator.validate_phone(data)


class ValidatedNameField(serializers.CharField):
    """Custom name field with validation."""

    def __init__(self, field_name="Name", **kwargs):
        self.field_name = field_name
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return BaseValidator.validate_name(data, self.field_name)


class ValidatedPasswordField(serializers.CharField):
    """Custom password field with strength validation."""

    def to_internal_value(self, data):
        return BaseValidator.validate_password(data)


# Utility functions for common validation scenarios
def validate_unique_email(email, exclude_id=None):
    """Check if email is unique in the system."""
    from apps.superadmin.models import Users

    email = BaseValidator.validate_email(email)
    query = Users.objects.filter(email=email)

    if exclude_id:
        query = query.exclude(id=exclude_id)

    if query.exists():
        raise ValidationError("User with this email already exists.")

    return email


def validate_department_exists(department_id):
    """Validate that department exists."""
    from apps.superadmin.models import Department

    if not department_id:
        return department_id

    if not Department.objects.filter(id=department_id).exists():
        raise ValidationError("Selected department does not exist.")

    return department_id


def validate_position_exists(position_id):
    """Validate that position exists."""
    from apps.superadmin.models import Position

    if not position_id:
        return position_id

    if not Position.objects.filter(id=position_id).exists():
        raise ValidationError("Selected position does not exist.")

    return position_id
