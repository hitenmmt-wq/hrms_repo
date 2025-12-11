from rest_framework import serializers
from apps.adminapp import models
from django.contrib.auth.hashers import make_password


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = '__all__'
        

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Holiday
        fields = '__all__'
        
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
