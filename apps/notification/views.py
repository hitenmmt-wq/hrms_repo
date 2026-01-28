# from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.base.pagination import CustomPageNumberPagination
from apps.base.permissions import IsAdmin, IsAuthenticated
from apps.base.response import ApiResponse
from apps.base.viewset import BaseViewSet
from apps.notification.custom_filters import NotificationFilter, NotificationTypeFilter
from apps.notification.models import DeviceToken, Notification, NotificationType
from apps.notification.serializers import (
    NotificationSerializer,
    NotificationTypeSerializer,
)
from apps.notification.websocket_service import NotificationWebSocketService

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
    ordering_fields = ["name"]
    ordering = ["name"]


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
    ordering_fields = ["-created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "actor__department", "actor__position", "notification_type", "content_type"
        )

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return ApiResponse.success({"unread_count": count})

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        NotificationWebSocketService.send_bulk_update(request.user.id, "all_read")
        return ApiResponse.success({"message": "Mark all notification as read."})


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        updated = (
            Notification.objects.filter(id=pk, recipient=request.user)
            .select_related("recipient")
            .update(is_read=True)
        )

        if updated:
            NotificationWebSocketService.send_count_update(request.user.id)
            return ApiResponse.success({"message": "Notification read"})

        return ApiResponse.error({"error": "Notification not found"}, status=404)


class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return ApiResponse.error({"error": "Token required"}, status=400)

        DeviceToken.objects.get_or_create(user=request.user, token=token)

        return ApiResponse.success({"Device token generated successfully": True})
