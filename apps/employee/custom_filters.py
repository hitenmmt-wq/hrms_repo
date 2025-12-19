import django_filters

from apps.employee.models import LeaveBalance, PaySlip
from apps.superadmin import models


class EmployeeFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(
        field_name="first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="last_name", lookup_expr="icontains"
    )
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    role = django_filters.CharFilter(field_name="role", lookup_expr="iexact")
    department = django_filters.NumberFilter(field_name="department__id")
    position = django_filters.NumberFilter(field_name="position__id")
    department_name = django_filters.CharFilter(
        field_name="department__name", lookup_expr="icontains"
    )
    position_name = django_filters.CharFilter(
        field_name="position__name", lookup_expr="icontains"
    )
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = models.Users
        fields = [
            "first_name",
            "last_name",
            "email",
            "role",
            "department",
            "department_name",
            "is_active",
        ]


class LeaveBalanceFilter(django_filters.FilterSet):
    employee = django_filters.NumberFilter(field_name="employee__id")
    year = django_filters.NumberFilter(field_name="year")
    pl = django_filters.NumberFilter(field_name="pl")
    sl = django_filters.NumberFilter(field_name="sl")
    lop = django_filters.NumberFilter(field_name="lop")

    class Meta:
        model = LeaveBalance
        fields = ["employee", "year", "pl", "sl", "lop"]


class ApplyLeaveFilter(django_filters.FilterSet):
    employee = django_filters.NumberFilter(field_name="employee__id")
    leave_type = django_filters.CharFilter(
        field_name="leave_type", lookup_expr="icontains"
    )
    from_date = django_filters.DateFilter(field_name="from_date", lookup_expr="date")
    to_date = django_filters.DateFilter(field_name="to_date", lookup_expr="date")
    total_days = django_filters.NumberFilter(field_name="total_days")
    reason = django_filters.CharFilter(field_name="reason", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")

    class Meta:
        models = models.Leave
        fields = [
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "total_days",
            "reason",
            "status",
        ]


class PaySlipFilter(django_filters.FilterSet):
    employee = django_filters.NumberFilter(field_name="employee__id")
    month = django_filters.CharFilter(field_name="month", lookup_expr="icontains")

    class Meta:
        model = PaySlip
        fields = ["employee", "month"]
