import django_filters

from apps.attendance import models


class EmployeeAttendanceFilter(django_filters.FilterSet):
    employee = django_filters.NumberFilter(field_name="employee__id")
    day = django_filters.DateFilter(field_name="day")
    check_in = django_filters.DateTimeFilter(field_name="check_in")
    check_out = django_filters.DateTimeFilter(field_name="check_out")
    status = django_filters.ChoiceFilter(
        choices=models.EmployeeAttendance.ATTENDANCE_TYPE
    )
    month = django_filters.NumberFilter(field_name="day", lookup_expr="month")
    year = django_filters.NumberFilter(field_name="day", lookup_expr="year")
    is_early_going = django_filters.BooleanFilter(field_name="is_early_going")
    is_late_coming = django_filters.BooleanFilter(field_name="is_late_coming")

    class Meta:
        model = models.EmployeeAttendance
        fields = [
            "employee",
            "day",
            "check_in",
            "check_out",
            "status",
            "month",
            "year",
            "is_early_going",
            "is_late_coming",
        ]
