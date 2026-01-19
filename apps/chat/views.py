import os

from django.shortcuts import get_object_or_404
from django.utils.text import get_valid_filename
from rest_framework import generics, status

# from rest_framework.decorators import action
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
from apps.employee.serializers import EmployeeListSerializer
from apps.superadmin.models import Users

# from django.utils import timezone
# from datetime import timedelta


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
    serializer_class = EmployeeListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_conversation_ids = Conversation.objects.filter(
            type="private", participants=user
        ).values_list("id", flat=True)

        connected_user_ids = (
            Users.objects.filter(conversations__id__in=user_conversation_ids)
            .exclude(id=user.id)
            .values_list("id", flat=True)
            .distinct()
        )

        remaining_users = (
            Users.objects.filter(
                is_active=True,
            )
            .exclude(id__in=connected_user_ids)
            .exclude(id=user.id)
            .select_related("department", "position")
        )
        return remaining_users


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


# class ChatSummaryView(generics.GenericAPIView):
#     """Get chat summary with unread counts and read receipts."""
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         user = request.user
#         conversations = Conversation.objects.filter(
#             participants=user, is_deleted=False
#         ).prefetch_related('participants', 'messages')

#         summary = []
#         total_unread = 0

#         for conv in conversations:
#             unread_count = conv.get_unread_count(user)
#             total_unread += unread_count

#             # Get last message
#             last_msg = conv.messages.filter(is_deleted=False).first()

#             # Get read receipts for user's messages
#             read_receipts = conv.get_read_receipts_for_sender(user)

#             summary.append({
#                 "conversation_id": conv.id,
#                 "conversation_type": conv.type,
#                 "conversation_name": conv.name,
#                 "unread_count": unread_count,
#                 "last_message": {
#                     "id": last_msg.id,
#                     "text": last_msg.text,
#                     "sender_id": last_msg.sender.id,
#                     "created_at": last_msg.created_at,
#                 } if last_msg else None,
#                 "read_receipts": read_receipts,
#             })

#         return ApiResponse.success({
#             "total_unread_messages": total_unread,
#             "conversations": summary
#         }, status=status.HTTP_200_OK)


# class MessagePollingView(generics.GenericAPIView):
#     """API endpoints for message polling when WebSocket is unavailable."""
#     permission_classes = [permissions.IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         """Get recent messages across all conversations."""
#         minutes = int(request.query_params.get('minutes', 5))
#         conversation_id = request.query_params.get('conversation_id')
#         last_message_id = request.query_params.get('last_message_id')

#         user_conversations = Conversation.objects.filter(participants=request.user)

#         query = Message.objects.filter(
#             conversation__in=user_conversations,
#             created_at__gt=timezone.now() - timedelta(minutes=minutes)
#         ).exclude(sender=request.user)

#         if conversation_id:
#             query = query.filter(conversation_id=conversation_id)

#         if last_message_id:
#             query = query.filter(id__gt=last_message_id)

#         messages = query.select_related('sender', 'conversation').order_by('-created_at')[:50]

#         messages_data = []
#         for msg in messages:
#             messages_data.append({
#                 'id': msg.id,
#                 'conversation_id': msg.conversation_id,
#                 'sender': msg.sender.email,
#                 'text': msg.text,
#                 'msg_type': msg.msg_type,
#                 'created_at': msg.created_at.isoformat()
#             })

#         return ApiResponse.success({
#             'messages': messages_data,
#             'count': len(messages_data),
#             'timestamp': timezone.now().isoformat()
#         }, status=status.HTTP_200_OK)

#     def post(self, request, *args, **kwargs):
#         """Send message via REST API."""
#         conversation_id = request.data.get('conversation_id')
#         content = request.data.get('content', '').strip()

#         if not conversation_id or not content:
#             return Response(
#                 {'error': 'conversation_id and content are required'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             conversation = get_object_or_404(
#                 Conversation.objects.prefetch_related('participants'),
#                 id=conversation_id
#             )

#             if not conversation.participants.filter(id=request.user.id).exists():
#                 return Response(
#                     {'error': 'Access denied'},
#                     status=status.HTTP_403_FORBIDDEN
#                 )

#             message = Message.objects.create(
#                 conversation=conversation,
#                 sender=request.user,
#                 text=content,
#                 msg_type='text'
#             )

#             # Create message status for participants
#             participants = conversation.participants.exclude(id=request.user.id)
#             for participant in participants:
#                 MessageStatus.objects.create(
#                     message=message,
#                     user=participant,
#                     status='sent'
#                 )

#             serializer = MessageSerializer(message)
#             return ApiResponse.success({
#                 'message': serializer.data
#             }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response(
#                 {'error': f'Failed to send message: {str(e)}'},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
