from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.chat import views

router = DefaultRouter()


urlpatterns = [
    path("", include(router.urls)),
]
