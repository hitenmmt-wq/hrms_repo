import django_filters

from apps.superadmin import models


class SuperAdminFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(
        field_name="first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="last_name", lookup_expr="icontains"
    )
    role = django_filters.CharFilter(field_name="role", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = models.Users
        fields = ["email", "first_name", "last_name", "role", "is_active"]


class HolidayFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    year = django_filters.NumberFilter(method="filter_year")

    class Meta:
        model = models.Holiday
        fields = ["name", "date"]

    def filter_year(self, queryset, name, value):
        return queryset.filter(date__year=value)


class AnnouncementFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    date = django_filters.DateFilter(field_name="date", lookup_expr="exact")

    class Meta:
        model = models.Announcement
        fields = ["title", "date"]


class DepartmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = models.Department
        fields = ["name"]


class PositionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = models.Position
        fields = ["name"]


class LeaveFilter(django_filters.FilterSet):
    employee = django_filters.CharFilter(
        field_name="employee__email", lookup_expr="icontains"
    )
    leave_type = django_filters.CharFilter(
        field_name="leave_type", lookup_expr="icontains"
    )
    status = django_filters.CharFilter(field_name="status", lookup_expr="icontains")
    from_date = django_filters.DateFilter(field_name="from_date", lookup_expr="gte")
    to_date = django_filters.DateFilter(field_name="to_date", lookup_expr="lte")

    class Meta:
        model = models.Leave
        fields = ["employee", "leave_type", "status", "from_date", "to_date"]
