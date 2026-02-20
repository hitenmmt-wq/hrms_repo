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
from apps.notification.models import Notification, NotificationType
from apps.notification.serializers import (
    NotificationSerializer,
    NotificationTypeSerializer,
)
from apps.notification.websocket_service import NotificationWebSocketService
from apps.superadmin.models import UserDeviceToken

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
        token = (
            request.data.get("token") or request.data.get("fcm_token") or ""
        ).strip()
        device_name = request.data.get("device_name", "").strip()

        device, created = UserDeviceToken.objects.get_or_create(
            user=request.user,
            fcm_token=token,
            device_name=device_name,
        )

        if not device:
            return ApiResponse.error(
                {"error": "Invalid or inactive tracking_token"},
                status=404,
            )

        if not created:
            if not device.is_active:
                device.is_active = True
            device.fcm_token = token
            device.save(
                update_fields=[
                    "fcm_token",
                    "device_name",
                    "tracking_token",
                    "is_active",
                ]
            )

        return ApiResponse.success(
            {
                "success": "Device token saved successfully",
            }
        )


class DeleteFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = (
            request.data.get("token") or request.data.get("fcm_token") or ""
        ).strip()

        device = UserDeviceToken.objects.filter(
            user=request.user, fcm_token=token
        ).first()

        if not device:
            return ApiResponse.error({"error": "Device not found"}, status=404)

        if token and device.fcm_token and device.fcm_token != token:
            return ApiResponse.error(
                {"error": "Token does not match device"}, status=400
            )

        device.is_active = False
        device.save(update_fields=["is_active"])
        return ApiResponse.success({"device_token_deleted": True})
