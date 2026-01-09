"""
Employee views for dashboard, profile management, leave applications, and payroll.

Handles employee-specific functionality including personal dashboard,
leave balance management, payslip generation, and employee CRUD operations
for admin users.
"""

import calendar

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.attendance.models import EmployeeAttendance
from apps.base import constants
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
from apps.employee.utils import employee_monthly_working_hours, generate_payslip_pdf
from apps.superadmin import models


class EmployeeDashboardView(APIView):
    """Employee personal dashboard with attendance, leave balance, and salary information."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get comprehensive employee dashboard data including attendance, leaves, and payroll info."""
        try:
            today = timezone.now().date()
            year = timezone.now().year
            current_month = timezone.now().month
            previous_month = (
                calendar.month_name[12]
                if current_month == 1
                else calendar.month_name[current_month - 1]
            )

            todays_attendance = (
                EmployeeAttendance.objects.filter(employee=request.user, day=today)
                .select_related("employee")
                .first()
            )

            employee_leave = (
                LeaveBalance.objects.filter(employee=request.user, year=year)
                .select_related("employee")
                .first()
            )

            common_data = models.CommonData.objects.first()
            if previous_month == "December":
                last_month_salary = (
                    PaySlip.objects.filter(
                        employee=request.user,
                        month=previous_month,
                        start_date__year=year - 1,
                    )
                    .select_related("employee")
                    .first()
                )
            else:
                last_month_salary = (
                    PaySlip.objects.filter(employee=request.user, month=previous_month)
                    .select_related("employee")
                    .first()
                )

            holiday_list = models.Holiday.objects.filter(
                date__year=timezone.now().year, date__gte=today
            ).order_by("date")
            upcoming_approved_leaves = (
                models.Leave.objects.filter(
                    status="approved", employee=request.user, from_date__gte=today
                )
                .select_related("leave_type")
                .order_by("from_date")[:5]
            )
            leave_history = (
                models.Leave.objects.filter(employee=request.user)
                .select_related("leave_type", "approved_by")
                .order_by("-id")[:5]
            )

            monthly_working_hours_data = employee_monthly_working_hours(request.user)

            # total_pl = employee_leave.pl if employee_leave.pl else common_data.pl_leave if common_data else None
            # total_sl = employee_leave.sl if employee_leave.sl else common_data.sl_leave if common_data else None
            return ApiResponse.success(
                data={
                    "attendance": TodayAttendanceSerializer(
                        todays_attendance, many=False
                    ).data,
                    "leave_calender": {
                        "total_pl": common_data.pl_leave if common_data else "",
                        "total_sl": common_data.sl_leave if common_data else "",
                        "available_pl": (
                            employee_leave.pl - employee_leave.used_pl
                            if employee_leave
                            else ""
                        ),
                        "available_sl": (
                            employee_leave.sl - employee_leave.used_sl
                            if employee_leave
                            else ""
                        ),
                    },
                    "last_month_salary": {
                        "total_earning": (
                            last_month_salary.total_earnings
                            if last_month_salary
                            else None
                        ),
                        "total_deduction": (
                            last_month_salary.total_deductions
                            if last_month_salary
                            else None
                        ),
                        "download_payslip": "",
                    },
                    "monthly_working_hours": monthly_working_hours_data,
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
    """Employee management ViewSet for admin operations."""

    queryset = models.Users.objects.filter(
        role="employee", is_active=True
    ).select_related("department", "position")
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
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action in ["update", "partial_update"]:
            return EmployeeUpdateSerializer
        return EmployeeListSerializer

    @action(detail=False, methods=["GET"])
    def present_employees(self, request):
        today = timezone.now().date()
        present_employee = EmployeeAttendance.objects.filter(
            day=today,
            employee__role=constants.EMPLOYEE_USER,
            employee__is_active=True,
            check_in__isnull=False,
        ).select_related("employee__department", "employee__position")
        present_employee_data = EmployeeListSerializer(present_employee, many=True).data

        return ApiResponse.success(present_employee_data)

    @action(detail=False, methods=["GET"])
    def absent_employees(self, request):
        today = timezone.now().date()
        present_employee_ids = EmployeeAttendance.objects.filter(
            day=today, check_in__isnull=False
        ).values_list("employee_id", flat=True)

        absent_employees = (
            models.Users.objects.filter(role=constants.EMPLOYEE_USER, is_active=True)
            .exclude(id__in=present_employee_ids)
            .select_related("department", "position")
        )
        absent_employee_data = EmployeeListSerializer(absent_employees, many=True).data
        return ApiResponse.success(absent_employee_data)


class LeaveBalanceViewSet(BaseViewSet):
    """Leave balance management for tracking employee leave allocations."""

    queryset = LeaveBalance.objects.select_related(
        "employee__department", "employee__position"
    ).order_by("-id")
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


class ApplyLeaveViewSet(BaseViewSet):
    """Leave application management for employees and admin approval."""

    queryset = models.Leave.objects.select_related(
        "employee__department", "employee__position", "leave_type", "approved_by"
    )
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
        "-id",
        "leave_type",
        "employee__email",
        "employee__role",
        "employee__first_name",
        "employee__last_name",
    ]
    ordering = ["-id"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return ApplyLeaveCreateSerializer
        return ApplyLeaveSerializer

    @action(detail=False, methods=["get"], url_path="employee_leave_list")
    def employee_leave_list(self, request):
        """Get leave history for the authenticated employee."""
        employee = request.user
        leaves = (
            models.Leave.objects.filter(employee=employee)
            .select_related("leave_type", "approved_by")
            .order_by("-id")
        )
        data = ApplyLeaveSerializer(leaves, many=True).data
        return ApiResponse.success(
            data=data, message="Employee leave list fetched successfully"
        )


class PaySlipViewSet(BaseViewSet):
    """Payslip management for employee salary processing and records."""

    queryset = PaySlip.objects.select_related(
        "employee__department", "employee__position"
    ).order_by("-id")
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
        """Return appropriate serializer based on action."""
        if self.action in ["create", "update", "partial_update"]:
            return PaySlipCreateSerializer
        return PaySlipSerializer

    @action(detail=False, methods=["get"], url_path="employee_payslips")
    def employee_payslips(self, request):
        """Get payslip history for the authenticated employee."""
        employee = request.user
        payslip = PaySlip.objects.filter(employee=employee).select_related("employee")
        data = PaySlipSerializer(payslip, many=True).data
        return ApiResponse.success(
            data=data, message="Employee payslip fetched successfully"
        )


class PaySlipDownloadView(APIView):
    """Payslip PDF download functionality for employees."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Generate and download payslip PDF for the specified payslip ID."""
        try:
            payslip = PaySlip.objects.select_related("employee").filter(pk=pk).first()
            if not payslip:
                return ApiResponse.error(message="Payslip not found", status=404)
            return generate_payslip_pdf(payslip)
        except Exception as e:
            return ApiResponse.error(message=str(e), status=400)
