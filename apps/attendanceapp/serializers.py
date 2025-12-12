from rest_framework import serializers
from apps.attendanceapp import models


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attendance
        fields = '__all__'
        depth = 1
        


class AttendanceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Attendance
        fields = '__all__'
        depth = 1
        
        
        