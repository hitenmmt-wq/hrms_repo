import os

from django.shortcuts import get_object_or_404
from django.utils.text import get_valid_filename
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.base import permissions
from apps.base.response import ApiResponse
from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus
from apps.chat.serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageReactionSerializer,
    MessageSerializer,
)

# Create your views here.


class CreateConversationView(generics.CreateAPIView):
    serializer_class = ConversationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        conv = serializer.save()
        conv.participants.add(self.request.user)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Conversation.objects.filter(participants=self.request.user)
            .prefetch_related("participants__department", "participants__position")
            .order_by("-created_at")
        )


class RemainingUsers(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset()


class ConversationDeleteView(generics.DestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return ApiResponse.success(
            {"message": "Conversation deleted successfully"}, status=status.HTTP_200_OK
        )


class FileUploadView(generics.CreateAPIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    ALLOWED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def post(self, request, *args, **kwargs):
        try:
            conv_id = request.data.get("conversation")
            if not conv_id:
                return Response(
                    {"error": "Conversation ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            conv = get_object_or_404(
                Conversation.objects.prefetch_related("participants"), id=conv_id
            )

            if not conv.participants.filter(id=request.user.id).exists():
                return Response(
                    {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
                )

            media_file = request.data.get("media")
            msg_type = request.data.get("msg_type", "text")

            # Validate file if provided
            if media_file and media_file != "file":
                if media_file.size > self.MAX_FILE_SIZE:
                    return Response(
                        {"error": "File size exceeds 10MB limit"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                file_ext = os.path.splitext(media_file.name)[1].lower()
                if file_ext not in self.ALLOWED_EXTENSIONS:
                    return Response(
                        {"error": "File type not allowed"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                media_file.name = get_valid_filename(media_file.name)

            serializer = MessageSerializer(
                data={
                    "conversation": conv.id,
                    "text": request.data.get("text", ""),
                    "reply_to_id": request.data.get("reply_to_id", ""),
                    "media": (
                        media_file if media_file and media_file != "file" else None
                    ),
                    "msg_type": msg_type,
                },
                context={"request": request},
            )

            if serializer.is_valid():
                serializer.save(sender=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": f"An error occurred while processing the file : {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConversationMessageView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conv = self.kwargs["conversation"]
        print(f"==>> conv: {conv}")
        return (
            Message.objects.filter(conversation=conv)
            .prefetch_related("sender__department", "sender__position")
            .order_by("-created_at")
        )


class MessageReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        msg_id = kwargs.get("message_id")
        msg = get_object_or_404(Message, id=msg_id)
        if msg:
            obj, created = MessageStatus.objects.get_or_create(
                message=msg, user=request.user, status="sent"
            )
            if created:
                print("createdd........")
            else:
                print("getted.....")
            obj.status = "read"
            obj.save()

        return ApiResponse.success(
            {"message": "Message marked as read"}, status=status.HTTP_200_OK
        )


class MessageReactionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Add reaction to a message."""
        message_id = kwargs.get("message_id")
        emoji = request.data.get("emoji")

        if not emoji:
            return Response(
                {"error": "Emoji is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        message = get_object_or_404(Message, id=message_id)

        # Check if user is participant in conversation
        if not message.conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
            )

        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=request.user,
            emoji=emoji,
            defaults={"is_deleted": False},
        )

        if not created and reaction.is_deleted:
            reaction.is_deleted = False
            reaction.save()
            created = True

        if created:
            serializer = MessageReactionSerializer(reaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"message": "Reaction already exists"}, status=status.HTTP_200_OK
            )

    def delete(self, request, *args, **kwargs):
        """Remove reaction from a message."""
        message_id = kwargs.get("message_id")
        emoji = request.data.get("emoji")

        if not emoji:
            return Response(
                {"error": "Emoji is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            reaction = MessageReaction.objects.get(
                message_id=message_id, user=request.user, emoji=emoji, is_deleted=False
            )
            reaction.is_deleted = True
            reaction.save()

            return ApiResponse.success(
                {"message": "Reaction removed successfully"}, status=status.HTTP_200_OK
            )
        except MessageReaction.DoesNotExist:
            return Response(
                {"error": "Reaction not found"}, status=status.HTTP_404_NOT_FOUND
            )
