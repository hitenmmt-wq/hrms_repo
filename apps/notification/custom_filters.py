import django_filters

from apps.notification import models


class NotificationTypeFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(field_name="code", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = models.NotificationType
        fields = ["code", "name"]


class NotificationFilter(django_filters.FilterSet):
    recipient = django_filters.CharFilter(
        field_name="recipient__email", lookup_expr="icontains"
    )
    actor = django_filters.CharFilter(
        field_name="actor__email", lookup_expr="icontains"
    )
    notification_type = django_filters.CharFilter(
        field_name="notification_type__name", lookup_expr="icontains"
    )
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    message = django_filters.CharFilter(field_name="message", lookup_expr="icontains")
    is_read = django_filters.BooleanFilter(field_name="is_read")

    class Meta:
        model = models.Notification
        fields = [
            "recipient",
            "actor",
            "notification_type",
            "title",
            "message",
            "is_read",
        ]
