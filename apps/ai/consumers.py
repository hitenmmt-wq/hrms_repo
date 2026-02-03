import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.serializers.json import DjangoJSONEncoder

from apps.ai.models import AIConversation, AIMessage, AIQueryLog
from apps.ai.services import AIService


class AIChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for AI chat functionality."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.room_name = f"ai_chat_{self.user.id}"
        self.room_group_name = f"ai_chat_{self.user.id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Send welcome message
        await self.send(
            text_data=json.dumps(
                {
                    "type": "ai_message",
                    "message": f"Hello {self.user.first_name}! I'm your HRMS AI assistant. How can I help you today?",
                    "timestamp": "time",
                }
            )
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if message_type == "user_message":
                await self.handle_user_message(text_data_json)
            elif message_type == "typing":
                await self.handle_typing_indicator(text_data_json)
            elif message_type == "response_feedback":
                await self.handle_feedback_response(text_data_json)
            elif message_type == "get_conversation_list":
                await self.handle_get_conversation_list()
            elif message_type == "get_message_details":
                await self.handle_get_message_details(text_data_json)
            elif message_type == "delete_conversation":
                await self.handle_delete_conversation(text_data_json)

        except json.JSONDecodeError:
            await self.send_error("Invalid message format")

    async def handle_user_message(self, data):
        """Process user message and generate AI response."""
        message = data.get("message", "").strip()
        conversation_id = data.get("conversation_id", "").strip()
        print(f"==>> message: {message}")

        if not message:
            await self.send_error("Message cannot be empty")
            return

        # Show typing indicator
        await self.send(text_data=json.dumps({"type": "ai_typing", "is_typing": True}))

        ai_service = AIService(self.user)
        print(f"==>> ai_service: {ai_service}")

        response = await ai_service.process_query(message, conversation_id)
        print(f"==>> response: {response}")

        await self.send(json.dumps({"type": "ai_typing", "is_typing": False}))

        await self.send(
            json.dumps(
                {
                    "type": "ai_message",
                    "conversation_id": response["conversation_id"],
                    "message": response,
                }
            )
        )

    async def handle_typing_indicator(self, data):
        """Handle typing indicator from user."""
        is_typing = data.get("is_typing", False)

        # Broadcast typing status back to user
        await self.send(
            text_data=json.dumps({"type": "user_typing", "is_typing": is_typing})
        )

    async def handle_feedback_response(self, data):
        """Handle user feedback on AI response."""
        feedback = data.get("feedback")
        ai_message_id = data.get("ai_message_id")

        await self.ai_feedback_save(self.user, feedback, ai_message_id)
        # Here you can log the feedback or process it as needed
        # await self.send(
        #     text_data=json.dumps(
        #         {"type": "feedback_received", "message": "Thank you for your feedback!"}
        #     )
        # )

    async def send_error(self, error_message):
        """Send error message to WebSocket."""
        return f"error handling not implemented yet : {error_message}"

    async def handle_get_conversation_list(self):
        """Handle request to get conversation list."""
        conversation_list = await self.get_conversation_list()
        await self.send(
            text_data=json.dumps(
                {"type": "conversation_list", "conversations": conversation_list}
            )
        )

    async def handle_get_message_details(self, data):
        """Handle request to get specific message details."""
        conversation_id = data.get("conversation_id")
        message_details = await self.get_message_details(conversation_id)
        await self.send(
            text_data=json.dumps(
                {"type": "message_details", "message": message_details},
                cls=DjangoJSONEncoder,
            )
        )

    async def handle_delete_conversation(self, data):
        """Handle request to delete a conversation."""
        conversation_id = data.get("conversation_id")
        await self.delete_conversation(conversation_id)
        await self.send(
            text_data=json.dumps(
                {"type": "conversation_deleted", "conversation_id": conversation_id}
            )
        )

    @database_sync_to_async
    def ai_feedback_save(self, user, feedback, ai_message_id):
        """Save AI response feedback to the database."""
        data = AIQueryLog.objects.filter(ai_message=ai_message_id).first()
        data.response_quality = feedback
        data.save()
        return data

    @database_sync_to_async
    def get_conversation_list(self):
        """Retrieve conversation list for the user."""
        data = (
            AIConversation.objects.filter(user=self.user)
            .order_by("-created_at")
            .values("id", "title", "session_id")
        )
        return list(data)

    @database_sync_to_async
    def get_message_details(self, conversation_id):
        """Retrieve detailed information about messages in a conversation."""
        data = (
            AIMessage.objects.filter(conversation_id=conversation_id)
            .order_by("-created_at")
            .values(
                "message_type", "content", "response_time", "metadata", "created_at"
            )
        )
        return list(data)

    @database_sync_to_async
    def delete_conversation(self, conversation_id):
        """Delete a conversation and its associated messages."""
        conversation = AIConversation.objects.get(id=conversation_id)
        conversation.delete()
        return "Conversation Deleted Successfully"
