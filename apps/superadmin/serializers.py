from rest_framework import serializers
from apps.superadmin import models
from apps.employee.models import LeaveBalance
from apps.attendance.models import EmployeeAttendance
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = '__all__'
        
class DepartmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = '__all__'
        
class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Announcement
        fields = '__all__'
        
class AnnouncementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Announcement
        fields = '__all__'
                
class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Position
        fields = '__all__'
        
class PositionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Position
        fields = '__all__'

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Holiday
        fields = '__all__'
        
class HolidayListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Holiday
        fields = "__all__"
        
        
# =============================================  DASHBOARD SERIALIZERS ================================================

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = ['id', 'email', 'role', 'birthdate', 'profile', 'first_name', 'last_name', 'department']
        
class HolidayMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Holiday
        fields = ['id', 'name', 'date']
        
class LeaveMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Leave
        fields = ['id', 'employee__first_name', 'employee__last_name', 'employee__email', 'start_date', 'end_date']
    
class LateLoginMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAttendance
        fields = ['id', 'employee__first_name', 'employee__last_name', 'employee__email', 'day', 'check_in']
        
        
#  ====================================================================================================================================================
class AdminRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = ['role','email','password']

    def create(self, validated_data):
        user = models.Users.objects.create(
            email=validated_data['email'],
            password=make_password(validated_data['password']),
            role=validated_data.get('role', 'employee'),
            is_active=False
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        print(f"==>> user: {user}")
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email or None,
            "role": self.user.role or None,
            "department": self.user.department.name if self.user.department else None,
            "profile": self.user.profile.url if self.user.profile else None,
            "first_name": self.user.first_name or None,
            "last_name": self.user.last_name or None,
        }
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = ['id', 'email', 'role', 'department', 'profile', 'first_name', 'last_name']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['department'] = instance.department.name if instance.department else None
        representation['profile'] = instance.profile.url if instance.profile else None
        return representation

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = ['first_name', 'last_name', 'email', 'role', 'department', 'profile']
        
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Users
        fields = ['first_name', 'last_name', 'profile']
        
class LeaveApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Leave
        fields = ["id", "leave_type", "start_date", "end_date", "reason"]

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError("end_date cannot be before start_date")
        # optionally check for future dates, max days, etc.
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        employee = request.user
        return models.apply_leave(employee, **validated_data)
    
class LeaveSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()

    class Meta:
        model = models.Leave
        fields = [
            "id", "employee", "leave_type", "from_date", "to_date",
            "total_days", "status", "reason", "approved_at", "approved_by", "response_text"
        ]
        read_only_fields = ["total_days", "status", "approved_at", "approved_by"]

    def get_employee(self, obj):
        return {
            "id": obj.employee.id,
            "email": obj.employee.email,
            "first_name": getattr(obj.employee, "first_name", ""),
            "last_name": getattr(obj.employee, "last_name", ""),
        }


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ["year", "pl", "sl", "lop"]
