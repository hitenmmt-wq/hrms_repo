from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.adminapp import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()

router.register('admin_register', views.AdminRegister, basename='admin_register')
router.register('holiday', views.HolidayViewSet, basename='holiday')
router.register('department', views.DepartmentViewSet, basename='department')
router.register('profile', views.ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path("activate/<str:token>/", views.ActivateUser.as_view(), name="activate_user"),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/user/', views.UserViewSet.as_view(), name='user'),
    
    path('auth/change_password/', views.ChangePassword.as_view(), name='change_password'),
    path('auth/reset_password/', views.ResetPassword.as_view(), name='reset_password'),
    # path('auth/confirm_reset_password/<str:token>/', views.ConfirmResetPassword.as_view(), name='confirm_reset_password'),
]
