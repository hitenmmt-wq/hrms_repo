from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.attendance import views

router = DefaultRouter()

router.register(
    r"employee_attendance", views.AttendanceViewSet, basename="employee_attendance"
)

urlpatterns = [
    path("", include(router.urls)),
    # path('auth/confirm_reset_password/<str:token>/', views.ConfirmResetPassword.as_view(), name='confirm_reset_password'),
]
