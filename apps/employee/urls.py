from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.employee import views

router = DefaultRouter()

router.register(r"employee", views.EmployeeViewSet, basename="employee")
router.register(r"leave_balance", views.LeaveBalanceViewSet, basename="leave_balance")
router.register(r"apply_leave", views.ApplyLeaveViewSet, basename="apply_leave")
router.register(r"pay_slip", views.PaySlipViewSet, basename="pay_slip")
router.register(r"ticket_issue", views.TicketIssueViewSet, basename="ticket_issue")

router.register(r"item", views.ItemViewSet, basename="item")
router.register(
    r"inventory_detail", views.InventoryDetailViewSet, basename="inventory_detail"
)
router.register(
    r"item_assignment", views.ItemAssignmentViewSet, basename="item_assignment"
)
router.register(r"item_history", views.ItemHistoryViewSet, basename="item_history")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "employee_dashboard/",
        views.EmployeeDashboardView.as_view(),
        name="employee_dashboard",
    ),
    path(
        "payslip_download/<int:pk>/",
        views.PaySlipDownloadView.as_view(),
        name="payslip_download",
    ),
]
