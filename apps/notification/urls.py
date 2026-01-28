from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notification import views

router = DefaultRouter()
router.register(
    "notification_type", views.NotificationTypeViewSet, basename="notification_type"
)
router.register("notifications", views.NotificationViewSet, basename="notifications")

urlpatterns = router.urls + [
    path("notifications/<int:pk>/read/", views.MarkAsReadView.as_view()),
    path("save-fcm-token/", views.SaveFCMTokenView.as_view()),
]
