# from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
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
    ordering_fields = ["title"]
    ordering = ["title"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "actor__department", "actor__position", "notification_type", "content_type"
        )

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        NotificationWebSocketService.send_bulk_update(request.user.id, "all_read")
        return Response({"status": "all marked as read"})


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        updated = (
            Notification.objects.filter(id=pk, recipient=request.user)
            .select_related("recipient")
            .update(is_read=True)
        )

        if updated:
            NotificationWebSocketService.send_read_update(request.user.id, pk)
            return Response({"status": "read"})

        return Response({"error": "Notification not found"}, status=404)
