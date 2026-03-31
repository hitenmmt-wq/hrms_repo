import django_filters

from apps.employee.models import (
    ExpenseClaim,
    InventoryDetail,
    Item,
    ItemAssignment,
    ItemHistory,
    LeaveBalance,
    PaySlip,
    TicketIssue,
)
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
    leave_type = django_filters.ModelChoiceFilter(
        field_name="leave_type", queryset=models.LeaveType.objects.all()
    )
    from_date = django_filters.DateFilter(field_name="from_date", lookup_expr="date")
    to_date = django_filters.DateFilter(field_name="to_date", lookup_expr="date")
    total_days = django_filters.NumberFilter(field_name="total_days")
    reason = django_filters.CharFilter(field_name="reason", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    month = django_filters.NumberFilter(method="filter_by_month_year")
    year = django_filters.NumberFilter(method="filter_by_month_year")

    class Meta:
        model = models.Leave
        fields = [
            "employee",
            "leave_type",
            "from_date",
            "to_date",
            "total_days",
            "reason",
            "status",
        ]

    def filter_by_month_year(self, queryset, name, value):
        month = self.data.get("month")
        year = self.data.get("year")
        if month:
            queryset = queryset.filter(from_date__month=int(month))

        if year:
            queryset = queryset.filter(from_date__year=int(year))

        return queryset


class PaySlipFilter(django_filters.FilterSet):
    employee = django_filters.NumberFilter(field_name="employee__id")
    month = django_filters.CharFilter(field_name="month", lookup_expr="icontains")

    class Meta:
        model = PaySlip
        fields = ["employee", "month"]


class TicketIssueFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    priority = django_filters.CharFilter(field_name="priority", lookup_expr="icontains")
    employee = django_filters.NumberFilter(field_name="employee__id")

    class Meta:
        model = TicketIssue
        fields = ["employee", "title", "status", "priority"]


class ItemFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    purchased_by = django_filters.NumberFilter(field_name="purchased_by__id")

    class Meta:
        model = Item
        fields = ["name", "purchased_by"]


class InventoryDetailFilter(django_filters.FilterSet):
    item = django_filters.NumberFilter(field_name="item__id")
    serial_number = django_filters.CharFilter(
        field_name="serial_number", lookup_expr="icontains"
    )
    purchase_date = django_filters.DateFilter(field_name="purchase_date")
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    condition = django_filters.CharFilter(
        field_name="condition", lookup_expr="icontains"
    )

    class Meta:
        model = InventoryDetail
        fields = ["serial_number", "item", "purchase_date", "status", "condition"]


class ItemAssignmentFilter(django_filters.FilterSet):
    inventory_item = django_filters.NumberFilter(field_name="inventory_item__id")
    employee = django_filters.NumberFilter(field_name="employee__id")
    assigned_date = django_filters.DateFilter(field_name="assigned_date")
    expected_return_date = django_filters.DateFilter(field_name="expected_return_date")
    actual_return_date = django_filters.DateFilter(field_name="actual_return_date")
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = ItemAssignment
        fields = [
            "inventory_item",
            "employee",
            "assigned_date",
            "expected_return_date",
            "actual_return_date",
            "is_active",
        ]


class ItemHistoryFilter(django_filters.FilterSet):
    inventory_item = django_filters.NumberFilter(field_name="inventory_item__id")
    action = django_filters.CharFilter(field_name="action", lookup_expr="icontains")
    employee = django_filters.NumberFilter(field_name="employee__id")
    date = django_filters.DateFilter(field_name="date")

    class Meta:
        model = ItemHistory
        fields = ["inventory_item", "action", "employee", "date"]


class ExpenseClaimFilter(django_filters.FilterSet):
    employee = django_filters.NumberFilter(field_name="employee__id")
    date = django_filters.DateFilter(field_name="date")
    amount = django_filters.NumberFilter(field_name="amount")
    description = django_filters.CharFilter(
        field_name="description", lookup_expr="icontains"
    )
    claim_status = django_filters.CharFilter(
        field_name="claim_status", lookup_expr="icontains"
    )
    clearance_status = django_filters.CharFilter(
        field_name="clearance_status", lookup_expr="icontains"
    )

    class Meta:
        model = ExpenseClaim
        fields = [
            "employee",
            "amount",
            "description",
            "claim_status",
            "clearance_status",
        ]
