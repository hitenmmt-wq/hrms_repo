# from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.viewset import BaseViewSet
from apps.notification.models import Notification, NotificationType
from apps.notification.serializers import (
    NotificationSerializer,
    NotificationTypeSerializer,
)

# from rest_framework.viewsets import ReadOnlyModelViewSet


# Create your views here.


class NotificationTypeViewSet(BaseViewSet):
    entity_name = "Notification Type"
    queryset = NotificationType.objects.all().order_by("-id")
    serializer_class = NotificationTypeSerializer


class NotificationViewSet(BaseViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        Notification.objects.filter(id=pk, recipient=request.user).update(is_read=True)
        return Response({"status": "read"})
