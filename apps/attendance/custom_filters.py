from django_filters import filters

from apps.attendance import models


class EmployeeAttendanceFilter(filters.Filter):
    employee = filters.NumberFilter(field_name="employee__id")
    day = filters.DateFilter(field_name="day")
    check_in = filters.DateTimeFilter(field_name="check_in")
    check_out = filters.DateTimeFilter(field_name="check_out")
    status = filters.ChoiceFilter(choice=models.EmployeeAttendance.ATTENDANCE_TYPE)

    class Meta:
        model = models.EmployeeAttendance
        fields = ["employee", "day", "check_in", "check_out", "status"]

    def filter_by_month(self, queryset, name, value):
        month = self.data.get("month")
        year = self.data.get("year")
        if month:
            queryset = queryset.filter(day__month=month)
        if year:
            queryset = queryset.filter(day__year=year)

        return queryset
