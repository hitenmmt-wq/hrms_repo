from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AIAnalyticsViewSet, AIConversationViewSet

router = DefaultRouter()
router.register(r"conversations", AIConversationViewSet, basename="ai-conversations")
router.register(r"analytics", AIAnalyticsViewSet, basename="ai-analytics")

urlpatterns = [
    path("", include(router.urls)),
]
