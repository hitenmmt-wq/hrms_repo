import django_filters
from apps.superadmin import models


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
