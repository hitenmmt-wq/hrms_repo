from django.shortcuts import render
from rest_framework.views import APIView
from apps.base.viewset import BaseViewSet
from apps.adminapp import models
from apps.adminapp import serializers
from apps.base.permissions import IsAdmin, IsEmployee, IsAuthenticated, IsHr
from apps.base.pagination import CustomPageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from apps.employee.custom_filters import EmployeeFilter
from rest_framework import filters
from apps.employee.models import LeaveBalance
from apps.employee.serializers import * #EmployeeListSerializer, LeaveBalanceSerializer, EmployeeUpdateSerializer, EmployeeCreateSerializer, ApplyLeaveCreateSerializer, ApplyLeaveSerializer
# Create your views here.


class EmployeeViewSet(BaseViewSet):
    queryset = models.Users.objects.filter(role="employee")
    serializer_class = EmployeeListSerializer
    entity_name = "Employee"
    permission_classes = [IsAdmin]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = ["employee_id","first_name","last_name","email","role","department__name", "position__name"]
    ordering_fields = ["employee_id","email", "role","first_name","last_name"]
    ordering = ["email"]
    
    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action in ["update", "partial_update"]:
            return EmployeeUpdateSerializer
        return EmployeeListSerializer
    
    
# ====================================================================== LEAVE-BALANCE CRUD API ===========================================================

class LeaveBalanceViewSet(BaseViewSet):
    queryset = LeaveBalance.objects.all().order_by("-id")
    serializer_class = LeaveBalanceSerializer
    entity_name = "Leave Balance"
    permission_classes = [IsAdmin]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["year","employee__email","employee__last_name","employee__first_name","employee__role","employee__department__name"]
    ordering_fields = ["employee__email", "employee__role", "employee__first_name", "employee__last_name"]
    ordering = ["year"]
    
    
# ====================================================================== LEAVE-BALANCE CRUD API ===========================================================

class ApplyLeaveViewSet(BaseViewSet):
    queryset = models.Leave.objects.all().order_by("-id")
    serializer_class = ApplyLeaveSerializer
    entity_name = "Apply Leave"
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["leave_type","employee__email","employee__last_name","employee__first_name", "from_date", "to_date", "status"]
    ordering_fields = ["leave_type","employee__email", "employee__role", "employee__first_name", "employee__last_name"]
    ordering = ["leave_type"]
    
    def get_serializer_class(self):
        if self.action == "create":
            return ApplyLeaveCreateSerializer
        return ApplyLeaveSerializer

    
    

    
    