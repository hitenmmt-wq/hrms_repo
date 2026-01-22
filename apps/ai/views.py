import logging

from django.db.models import Avg
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ai.models import AIConversation, AIMessage, AIQueryLog
from apps.ai.serializers import (
    AIConversationSerializer,
    AIMessageSerializer,
    AIQueryLogSerializer,
)
from apps.ai.services import AIService
from apps.base.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


class AIConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI conversations."""

    serializer_class = AIConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return conversations for current user."""
        return AIConversation.objects.filter(user=self.request.user).order_by(
            "-updated_at"
        )

    def perform_create(self, serializer):
        """Create conversation for current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        """Get messages for a specific conversation."""
        conversation = self.get_object()
        messages = AIMessage.objects.filter(conversation=conversation).order_by(
            "created_at"
        )
        serializer = AIMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Send message to AI in specific conversation."""
        conversation = self.get_object()
        message = request.data.get("message", "").strip()

        if not message:
            return Response(
                {"error": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ai_service = AIService(request.user)
            response_data = ai_service.process_query(message, conversation.session_id)
            print(f"==>> response_data: {response_data}")

            return Response(
                {
                    "success": True,
                    "ai_response": response_data["response"],
                    "message_id": response_data["message_id"],
                    "processing_time": response_data["processing_time"],
                    "intent": response_data.get("intent", "unknown"),
                }
            )

        except Exception as e:
            logger.exception(f"Error processing message for user {request.user.id}")
            return Response(
                {"error": f"Failed to process message: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def quick_query(self, request):
        """Send a quick query without creating a persistent conversation."""
        message = request.data.get("message", "").strip()

        if not message:
            return Response(
                {"error": "Message cannot be empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ai_service = AIService(request.user)
            response_data = ai_service.process_query(message)

            return Response(
                {
                    "success": True,
                    "response": response_data["response"],
                    "conversation_id": response_data["conversation_id"],
                    "processing_time": response_data["processing_time"],
                    "intent": response_data.get("intent", "unknown"),
                }
            )

        except Exception as e:
            logger.exception(f"Error processing quick query for user {request.user.id}")
            return Response(
                {"error": f"Failed to process query: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI analytics and query logs."""

    serializer_class = AIQueryLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return query logs based on user role."""
        if self.request.user.role in ["admin", "hr"]:
            # Admin/HR can see all query logs
            return AIQueryLog.objects.all().order_by("-created_at")
        else:
            # Regular users see only their own logs
            return AIQueryLog.objects.filter(user=self.request.user).order_by(
                "-created_at"
            )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get AI usage statistics."""
        queryset = self.get_queryset()

        stats = {
            "total_queries": queryset.count(),
            "unique_users": (
                queryset.values("user").distinct().count()
                if request.user.role in ["admin", "hr"]
                else 1
            ),
            "popular_intents": list(
                queryset.values("intent").exclude(intent__isnull=True).distinct()[:5]
            ),
            "avg_response_time": queryset.filter(
                processing_time__isnull=False
            ).aggregate(avg_time=Avg("processing_time"))["avg_time"]
            or 0,
        }

        return Response(stats)

    @action(detail=False, methods=["post"])
    def rate_response(self, request):
        """Rate an AI response quality."""
        query_id = request.data.get("query_id")
        rating = request.data.get("rating")

        if not query_id or not rating:
            return Response(
                {"error": "query_id and rating are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if rating not in [1, 2, 3, 4, 5]:
            return Response(
                {"error": "Rating must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            query_log = AIQueryLog.objects.get(id=query_id, user=request.user)
            query_log.response_quality = rating
            query_log.save()

            return Response({"success": True, "message": "Rating saved successfully"})

        except AIQueryLog.DoesNotExist:
            return Response(
                {"error": "Query not found"}, status=status.HTTP_404_NOT_FOUND
            )
