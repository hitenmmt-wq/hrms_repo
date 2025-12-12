from django.shortcuts import render

# Create your views here.


from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from django.shortcuts import get_object_or_404


class CreateConversationView(generics.CreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]


    def perform_create(self, serializer):
        conv = serializer.save()
        conv.participants.add(self.request.user)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).order_by('-created_at')


class FileUploadView(generics.CreateAPIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer 


    def post(self, request, *args, **kwargs):
        conv_id = request.data.get('conversation')
        conv = get_object_or_404(Conversation, id=conv_id)
        f = request.data.get('media')
        msg_type = request.data.get('msg_type', 'file')

        msg = Message.objects.create(
            conversation=conv,
            sender=request.user,
            media=f,
            msg_type=msg_type
        )
        serializer = MessageSerializer(msg, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)