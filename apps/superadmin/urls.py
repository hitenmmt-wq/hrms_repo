"""
URL configuration for superadmin app.

Defines URL patterns for admin functionality including user management,
organizational structure, authentication, leave management, and system configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.superadmin import views

router = DefaultRouter()

router.register(r"common_data", views.CommonDataViewSet, basename="common_data")
router.register(r"setting_data", views.SettingDataViewSet, basename="setting_data")
router.register(r"admin_register", views.AdminRegister, basename="admin_register")
router.register(r"holiday", views.HolidayViewSet, basename="holiday")
router.register(r"department", views.DepartmentViewSet, basename="department")
router.register(r"announcement", views.AnnouncementViewSet, basename="announcement")
router.register(r"position", views.PositionViewSet, basename="position")
router.register(r"profile", views.ProfileViewSet, basename="profile")
router.register(r"leave", views.LeaveViewSet, basename="leave")
router.register(r"leave_type", views.LeaveTypeViewSet, basename="leave_type")

urlpatterns = [
    path("", include(router.urls)),
    path("custom_script/", views.CustomScriptView.as_view(), name="custom_script"),
    path(
        "admin_dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"
    ),
    # path("activate/<str:token>/", views.ActivateUser.as_view(), name="activate_user"),
    path(
        "auth/login/",
        views.CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/user/", views.UserViewSet.as_view(), name="user"),
    path(
        "auth/change_password/", views.ChangePassword.as_view(), name="change_password"
    ),
    path("auth/reset_password/", views.ResetPassword.as_view(), name="reset_password"),
    path(
        "auth/confirm_reset_password/",
        views.ConfirmResetPassword.as_view(),
        name="confirm_reset_password",
    ),
    path(
        "leave/<int:pk>/approve/",
        views.LeaveApprovalViewSet.as_view({"post": "approve"}),
        name="leave-approve",
    ),
    path(
        "leave/<int:pk>/reject/",
        views.LeaveApprovalViewSet.as_view({"post": "reject"}),
        name="leave-reject",
    ),
    path(
        "leave_balance_details/",
        views.LeaveApprovalViewSet.as_view({"get": "leave_balance_details"}),
        name="leave_balance_details",
    ),
    path("activity-log/", views.ActivityLogAPI.as_view(), name="activity-log"),
    path("device/register/", views.DeviceRegisterAPI.as_view(), name="device-register"),
]
