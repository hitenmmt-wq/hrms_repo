from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notification.views import (
    MarkAsReadView,
    NotificationTypeViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register(
    "notification_type", NotificationTypeViewSet, basename="notification_type"
)
router.register("notifications", NotificationViewSet, basename="notifications")

urlpatterns = router.urls + [
    path("notifications/<int:pk>/read/", MarkAsReadView.as_view()),
]
