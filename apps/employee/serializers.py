from rest_framework import serializers
from apps.adminapp import models
from apps.employee.models import LeaveBalance


#  ==================================== EMPLOYEE SERIALIZER ======================================================================

class EmployeeCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    department = serializers.PrimaryKeyRelatedField(queryset=models.Department.objects.all())
    position = serializers.PrimaryKeyRelatedField(queryset=models.Position.objects.all())
    class Meta:
        model = models.Users
        fields = ["first_name", "last_name", "email", "role", "department", "position", "employee_id", "password", "joining_date"]
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
        fields = ["id", "first_name", "last_name", "email", "role", "department", "position", "employee_id", "joining_date", "is_active"]
        depth = 1
        
class EmployeeUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    department = serializers.PrimaryKeyRelatedField(queryset=models.Department.objects.all())
    position = serializers.PrimaryKeyRelatedField(queryset=models.Position.objects.all())
    class Meta:
        model = models.Users
        fields = ["id", "first_name", "last_name", "email", "role", "department", "position", "employee_id", "password", "joining_date"]
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
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())
    # approved_by = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())
    
    class Meta:
        model = models.Leave
        fields = ["id", "employee", "leave_type", "from_date", "to_date", "total_days", "reason", "status"]
        depth = 1
        

class ApplyLeaveCreateSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())
    # approved_by = serializers.PrimaryKeyRelatedField(queryset=models.Users.objects.all())
    
    class Meta:
        model = models.Leave
        fields = ["id", "employee", "leave_type", "from_date", "to_date", "total_days", "reason", "status"]
        
        
