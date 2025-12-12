from django.shortcuts import render
from rest_framework.views import APIView
from apps.base.viewset import BaseViewSet
from apps.adminapp import models
from apps.adminapp import serializers
from apps.base.permissions import IsAdmin, IsEmployee, IsAuthenticated, IsHr
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

# Create your views here.


class EmployeeAttendanceViewSet(BaseViewSet):
    queryset = models.Attendance.objects.all().order_by("-id")
    serializers_class = serializers.EmployeeAttendanceSerializer
    
    