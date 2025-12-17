from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.employee import views

router = DefaultRouter()

router.register(r"employee", views.EmployeeViewSet, basename="employee")
router.register(r"leave_balance", views.LeaveBalanceViewSet, basename="leave_balance")
router.register(r"apply_leave", views.ApplyLeaveViewSet, basename="apply_leave")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "employee_dashboard/",
        views.EmployeeDashboardView.as_view(),
        name="employee_dashboard",
    ),
]
