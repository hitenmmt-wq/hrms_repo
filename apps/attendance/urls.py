from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.attendance import views

router = DefaultRouter()

router.register(
    r"employee_attendance", views.AttendanceViewSet, basename="employee_attendance"
)

urlpatterns = [
    path("", include(router.urls)),
]
