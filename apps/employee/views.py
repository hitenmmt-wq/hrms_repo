from datetime import date

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.attendance.models import EmployeeAttendance
from apps.base.pagination import CustomPageNumberPagination
from apps.base.permissions import IsAdmin, IsAuthenticated
from apps.base.response import ApiResponse
from apps.base.viewset import BaseViewSet
from apps.employee.custom_filters import (
    ApplyLeaveFilter,
    EmployeeFilter,
    LeaveBalanceFilter,
    PaySlipFilter,
)
from apps.employee.models import LeaveBalance, PaySlip
from apps.employee.serializers import (
    ApplyLeaveCreateSerializer,
    ApplyLeaveSerializer,
    EmployeeCreateSerializer,
    EmployeeListSerializer,
    EmployeeUpdateSerializer,
    HolidayMiniSerializer,
    LeaveBalanceSerializer,
    LeaveMiniSerializer,
    PaySlipCreateSerializer,
    PaySlipSerializer,
    TodayAttendanceSerializer,
)
from apps.superadmin import models

# Create your views here.


class EmployeeDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            today = timezone.now().date()
            year = timezone.now().year
            year_start = date(year, 1, 1)
            print(f"==>> year_start: {year_start}")
            year_end = date(year, 12, 31)
            print(f"==>> year_end: {year_end}")

            todays_attendance = EmployeeAttendance.objects.filter(
                employee=request.user, day=today
            ).first()
            print(f"==>> request.user: {request.user}")
            print(f"==>> todays_attendance: {todays_attendance}")

            employee_leave = LeaveBalance.objects.filter(
                employee=request.user, year=year
            ).first()

            common_data = models.CommonData.objects.first()
            # last_month_salary = ""

            # monthly_working_hours = ""

            holiday_list = models.Holiday.objects.filter(
                date__year=timezone.now().year
            ).order_by("date")
            upcoming_approved_leaves = models.Leave.objects.filter(
                status="approved", employee=request.user, from_date__gte=today
            ).order_by("-id")[:5]
            leave_history = models.Leave.objects.filter(employee=request.user).order_by(
                "-id"
            )[:5]

            return ApiResponse.success(
                data={
                    "attendance": TodayAttendanceSerializer(
                        todays_attendance, many=False
                    ).data,
                    "leave_calender": {
                        "total_pl": common_data.pl_leave if common_data else "",
                        "total_sl": common_data.sl_leave if common_data else "",
                        "available_pl": employee_leave.pl if employee_leave else "",
                        "available_sl": employee_leave.sl if employee_leave else "",
                    },
                    "salary": " ",
                    "holiday_list": HolidayMiniSerializer(holiday_list, many=True).data,
                    "upcoming_approved_leaves": LeaveMiniSerializer(
                        upcoming_approved_leaves, many=True
                    ).data,
                    "leave_history": LeaveMiniSerializer(leave_history, many=True).data,
                },
                message="Employee dashboard data fetched successfully",
            )
        except Exception as e:
            return ApiResponse.error(
                message="Failed to load dashboard", errors=str(e), status=500
            )


class EmployeeViewSet(BaseViewSet):
    queryset = models.Users.objects.filter(role="employee")
    serializer_class = EmployeeListSerializer
    entity_name = "Employee"
    permission_classes = [IsAdmin]
    pagination_class = CustomPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = EmployeeFilter
    search_fields = [
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "role",
        "department__name",
        "position__name",
    ]
    ordering_fields = ["employee_id", "email", "role", "first_name", "last_name"]
    ordering = ["email"]

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action in ["update", "partial_update"]:
            return EmployeeUpdateSerializer
        return EmployeeListSerializer


#   ============ LEAVE-BALANCE CRUD API   =


class LeaveBalanceViewSet(BaseViewSet):
    queryset = LeaveBalance.objects.all().order_by("-id")
    serializer_class = LeaveBalanceSerializer
    entity_name = "Leave Balance"
    permission_classes = [IsAdmin]
    pagination_class = CustomPageNumberPagination
    filterset_class = LeaveBalanceFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "year",
        "employee__email",
        "employee__last_name",
        "employee__first_name",
        "employee__role",
        "employee__department__name",
    ]
    ordering_fields = [
        "employee__email",
        "employee__role",
        "employee__first_name",
        "employee__last_name",
    ]
    ordering = ["year"]


#   ============ LEAVE-BALANCE CRUD API   =


class ApplyLeaveViewSet(BaseViewSet):
    queryset = models.Leave.objects.all().order_by("-id")
    serializer_class = ApplyLeaveSerializer
    entity_name = "Apply Leave"
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filterset_class = ApplyLeaveFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "leave_type",
        "employee__email",
        "employee__last_name",
        "employee__first_name",
        "from_date",
        "to_date",
        "status",
    ]
    ordering_fields = [
        "leave_type",
        "employee__email",
        "employee__role",
        "employee__first_name",
        "employee__last_name",
    ]
    ordering = ["leave_type"]

    def get_serializer_class(self):
        if self.action == "create":
            return ApplyLeaveCreateSerializer
        return ApplyLeaveSerializer

    @action(detail=False, methods=["get"], url_path="employee_leave_list")
    def employee_leave_list(self, request):
        employee = request.user
        leaves = models.Leave.objects.filter(employee=employee).order_by("-id")
        data = ApplyLeaveSerializer(leaves, many=True).data
        return ApiResponse.success(
            data=data, message="Employee leave list fetched successfully"
        )


# ======== EMPLOYEE PAYSLIP VIEWSET ============


class PaySlipViewSet(BaseViewSet):
    queryset = PaySlip.objects.all().order_by("-id")
    serializer_class = PaySlipSerializer
    entity_name = "Pay Slip"
    permission_classes = [IsAdmin]
    pagination_class = CustomPageNumberPagination
    filterset_class = PaySlipFilter
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "employee__email",
        "month",
    ]
    ordering_fields = [
        "employee__email",
        "month",
    ]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PaySlipCreateSerializer
        return PaySlipSerializer
