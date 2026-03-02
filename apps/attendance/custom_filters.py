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

    class Meta:
        model = models.EmployeeAttendance
        fields = ["employee", "day", "check_in", "check_out", "status", "month", "year"]
