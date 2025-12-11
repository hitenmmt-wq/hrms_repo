from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.adminapp import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()

router.register('admin_register', views.AdminRegister, basename='admin_register')
router.register('holiday', views.HolidayViewSet, basename='holiday')
router.register('department', views.DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
    path("activate/<str:token>/", views.ActivateUser.as_view(), name="activate-user"),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
