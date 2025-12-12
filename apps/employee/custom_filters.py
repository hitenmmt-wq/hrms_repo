import django_filters
from apps.adminapp import models


class EmployeeFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(field_name="first_name", lookup_expr="icontains")
    last_name = django_filters.CharFilter(field_name="last_name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    role = django_filters.CharFilter(field_name="role", lookup_expr="iexact")
    department = django_filters.NumberFilter(field_name="department__id")
    position = django_filters.NumberFilter(field_name="position__id")
    department_name = django_filters.CharFilter(field_name="department__name", lookup_expr="icontains")
    position_name = django_filters.CharFilter(field_name="position__name", lookup_expr="icontains")
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
