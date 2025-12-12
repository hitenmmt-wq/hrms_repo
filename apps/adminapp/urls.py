from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.adminapp import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()

router.register(r'admin_register', views.AdminRegister, basename='admin_register')
router.register(r'holiday', views.HolidayViewSet, basename='holiday')
router.register(r'department', views.DepartmentViewSet, basename='department')
router.register(r'position', views.PositionViewSet, basename='position')
router.register(r'profile', views.ProfileViewSet, basename='profile')
router.register(r"leave", views.LeaveViewSet, basename="leave")

urlpatterns = [
    path('', include(router.urls)),
    path("activate/<str:token>/", views.ActivateUser.as_view(), name="activate_user"),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/user/', views.UserViewSet.as_view(), name='user'),
    
    path('auth/change_password/', views.ChangePassword.as_view(), name='change_password'),
    path('auth/reset_password/', views.ResetPassword.as_view(), name='reset_password'),
    path('auth/reset_password_change/', views.ResetPasswordChange.as_view(), name='reset_password_change'),
    # path('auth/confirm_reset_password/<str:token>/', views.ConfirmResetPassword.as_view(), name='confirm_reset_password'),
    
    path("leave/<int:pk>/approve/", views.LeaveApprovalViewSet.as_view({"post": "approve"}), name="leave-approve"),
    path("leave/<int:pk>/reject/", views.LeaveApprovalViewSet.as_view({"post": "reject"}), name="leave-reject"),

]
