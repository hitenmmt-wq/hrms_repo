"""
Superadmin serializers for HRMS data serialization and validation.

Provides serializers for user management, organizational structure,
leave management, authentication, and dashboard data formatting.
Handles data validation and transformation for API responses.
"""

from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.attendance.models import EmployeeAttendance
from apps.employee.models import LeaveBalance
from apps.employee.serializers import EmployeeListSerializer
from apps.superadmin import models


class CommonDataSerializer(serializers.ModelSerializer):
    """Serializer for company configuration and leave policy settings."""

    class Meta:
        model = models.CommonData
        fields = "__all__"


class SettingDataSerializer(serializers.ModelSerializer):
    """Serializer for system configuration settings."""

    class Meta:
        model = models.SettingData
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for department CRUD operations."""

    class Meta:
        model = models.Department
        fields = "__all__"


class DepartmentListSerializer(serializers.ModelSerializer):
    """Serializer for department list display."""

    class Meta:
        model = models.Department
        fields = "__all__"


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for company announcements."""

    class Meta:
        model = models.Announcement
        fields = "__all__"


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Serializer for announcement list display."""

    class Meta:
        model = models.Announcement
        fields = "__all__"


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for job positions."""

    class Meta:
        model = models.Position
        fields = "__all__"


class PositionListSerializer(serializers.ModelSerializer):
    """Serializer for position list display."""

    class Meta:
        model = models.Position
        fields = "__all__"


class HolidaySerializer(serializers.ModelSerializer):
    """Serializer for company holidays."""

    class Meta:
        model = models.Holiday
        fields = "__all__"


class HolidayListSerializer(serializers.ModelSerializer):
    """Serializer for holiday list display."""

    class Meta:
        model = models.Holiday
        fields = "__all__"


class LeaveTypeSerializer(serializers.ModelSerializer):
    """Serializer for leave types configuration."""

    class Meta:
        model = models.LeaveType
        fields = "__all__"


#  ================  DASHBOARD SERIALIZERS  ===================


class UserMiniSerializer(serializers.ModelSerializer):
    """Minimal user serializer for dashboard and list displays."""

    profile = serializers.SerializerMethodField()

    class Meta:
        model = models.Users
        fields = [
            "id",
            "email",
            "role",
            "birthdate",
            "profile",
            "first_name",
            "last_name",
            "department",
        ]
        depth = 1

    def get_profile(self, obj):
        request = self.context.get("request")
        if obj.profile and request:
            return request.build_absolute_uri(obj.profile.url)
        if obj.profile:
            return obj.profile.url
        return None


class HolidayMiniSerializer(serializers.ModelSerializer):
    """Minimal holiday serializer for dashboard display."""

    class Meta:
        model = models.Holiday
        fields = ["id", "name", "date"]


class LeaveMiniSerializer(serializers.ModelSerializer):
    """Minimal leave serializer for dashboard display."""

    employee = EmployeeListSerializer()

    class Meta:
        model = models.Leave
        fields = [
            "id",
            "employee",
            "from_date",
            "to_date",
        ]


class LateLoginMiniSerializer(serializers.ModelSerializer):
    """Serializer for late login attendance records."""

    employee = EmployeeListSerializer()

    class Meta:
        model = EmployeeAttendance
        fields = ["id", "employee", "day", "check_in"]


class EmployeeAttendanceMiniSerializer(serializers.ModelSerializer):
    """Minimal attendance serializer for dashboard display."""

    employee = EmployeeListSerializer()

    class Meta:
        model = EmployeeAttendance
        fields = ["id", "employee", "check_in", "check_out"]


#       ====================
class AdminRegisterSerializer(serializers.ModelSerializer):
    """Serializer for admin user registration with password hashing."""

    class Meta:
        model = models.Users
        fields = ["role", "email", "password", "birthdate", "joining_date"]

    def create(self, validated_data):
        """Create admin user with hashed password and inactive status."""
        user = models.Users.objects.create(
            email=validated_data["email"],
            password=make_password(validated_data["password"]),
            role=validated_data.get("role", "employee"),
            birthdate=validated_data.get("birthdate", None),
            joining_date=validated_data.get("joining_date", None),
            is_active=True,
        )
        return user


class AdminListSerializer(serializers.ModelSerializer):
    """Serializer for admin user list display."""

    class Meta:
        model = models.Users
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "joining_date",
            "birthdate",
            "is_active",
        ]


class AdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin user profile updates."""

    class Meta:
        model = models.Users
        fields = ["first_name", "last_name", "is_active", "role", "birthdate"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with user role and profile data."""

    @classmethod
    def get_token(cls, user):
        """Add user role to JWT token payload."""
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        """Add user profile data to token response."""
        data = super().validate(attrs)
        request = self.context.get("request")

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email or None,
            "role": self.user.role or None,
            "department": self.user.department.name if self.user.department else None,
            "profile": (
                request.build_absolute_uri(self.user.profile.url)
                if self.user.profile
                else None
            ),
            "first_name": self.user.first_name or None,
            "last_name": self.user.last_name or None,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile data with department and profile URL."""

    department = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = models.Users
        fields = [
            "id",
            "email",
            "role",
            "department",
            "profile",
            "first_name",
            "last_name",
            "salary_ctc",
        ]

    def get_department(self, obj):
        return obj.department.name if obj.department else None

    def get_profile(self, obj):
        request = self.context.get("request")
        if obj.profile:
            if request:
                return request.build_absolute_uri(obj.profile.url)
            return obj.profile.url
        return None


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display."""

    profile = serializers.SerializerMethodField()

    class Meta:
        model = models.Users
        fields = ["first_name", "last_name", "email", "role", "department", "profile"]

    def get_profile(self, obj):
        request = self.context.get("request")
        if obj.profile and request:
            return request.build_absolute_uri(obj.profile.url)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates."""

    class Meta:
        model = models.Users
        fields = ["first_name", "last_name", "profile"]


class LeaveApplySerializer(serializers.ModelSerializer):
    """Serializer for leave application with date validation."""

    class Meta:
        model = models.Leave
        fields = ["id", "leave_type", "from_date", "to_date", "reason", "day_part"]

    def validate(self, attrs):
        """Validate that end date is not before start date."""
        if attrs["to_date"] < attrs["from_date"]:
            raise serializers.ValidationError("end_date cannot be before start_date")
        return attrs

    def create(self, validated_data):
        """Create leave application for authenticated user."""
        request = self.context["request"]
        employee = request.user
        validated_data["employee"] = employee
        return models.Leave.objects.create(**validated_data)


class LeaveSerializer(serializers.ModelSerializer):
    """Serializer for leave records with employee and leave type details."""

    employee = EmployeeListSerializer()
    leave_type = LeaveTypeSerializer()

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
            "status",
            "reason",
            "approved_at",
            "approved_by",
            "response_text",
        ]
        read_only_fields = ["total_days", "status", "approved_at", "approved_by"]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for employee leave balance information."""

    class Meta:
        model = LeaveBalance
        fields = ["year", "pl", "sl", "lop"]
