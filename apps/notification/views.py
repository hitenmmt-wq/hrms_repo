# from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.pagination import CustomPageNumberPagination
from apps.base.permissions import IsAdmin, IsAuthenticated
from apps.base.viewset import BaseViewSet
from apps.notification.custom_filters import NotificationFilter, NotificationTypeFilter
from apps.notification.models import Notification, NotificationType
from apps.notification.serializers import (
    NotificationSerializer,
    NotificationTypeSerializer,
)

# from rest_framework.viewsets import ReadOnlyModelViewSet


# Create your views here.


class NotificationTypeViewSet(BaseViewSet):
    entity_name = "Notification Type"
    permission_classes = [IsAdmin]
    queryset = NotificationType.objects.all().order_by("-id")
    serializer_class = NotificationTypeSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = NotificationTypeFilter
    search_fields = ["name"]
    ordering_fields = ["date", "name"]
    ordering = ["date"]


class NotificationViewSet(BaseViewSet):
    entity_name = "Notification"
    permission_classes = [IsAdmin]
    serializer_class = NotificationSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = NotificationFilter
    search_fields = ["title"]
    ordering_fields = ["title"]
    ordering = ["title"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        Notification.objects.filter(id=pk, recipient=request.user).update(is_read=True)
        return Response({"status": "read"})
