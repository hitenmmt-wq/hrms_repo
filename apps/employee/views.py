from django.shortcuts import render
from rest_framework.views import APIView
from apps.base.viewset import BaseViewSet
from apps.superadmin import models
from apps.superadmin import serializers
from apps.base.permissions import IsAdmin, IsEmployee, IsAuthenticated, IsHr
from apps.base.pagination import CustomPageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from apps.employee.custom_filters import EmployeeFilter, ApplyLeaveFilter, LeaveBalanceFilter
from rest_framework import filters
from apps.employee.models import LeaveBalance
from django.utils import timezone
from apps.employee.serializers import * #EmployeeListSerializer, LeaveBalanceSerializer, EmployeeUpdateSerializer, EmployeeCreateSerializer, ApplyLeaveCreateSerializer, ApplyLeaveSerializer
# Create your views here.


class EmployeeDashboardView(APIView):
    def get(self, request):
        try:
                
            today = timezone.now().date()
            holiday_list = models.Holiday.objects.filter(date__year=timezone.now().year).order_by("date")
            upcoming_approved_leaves = models.Leave.objects.filter(status="approved", employee=request.user, date__gte=today).order_by("-id")[:5]
            leave_history = models.Leave.objects.filter(employee=request.user).order_by("-id")[:5]
            
            attendance = ""
            leave_calender = ""
            salary = ""
            
        except Exception as e:
            return ApiResponse.error(message="Failed to load dashboard",errors=str(e), status=500)
        

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
    filterset_class = LeaveBalanceFilter
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
    filterset_class = ApplyLeaveFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["leave_type","employee__email","employee__last_name","employee__first_name", "from_date", "to_date", "status"]
    ordering_fields = ["leave_type","employee__email", "employee__role", "employee__first_name", "employee__last_name"]
    ordering = ["leave_type"]
    
    def get_serializer_class(self):
        if self.action == "create":
            return ApplyLeaveCreateSerializer
        return ApplyLeaveSerializer

    
    

    
    