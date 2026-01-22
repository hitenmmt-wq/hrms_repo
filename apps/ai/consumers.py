import json

from channels.generic.websocket import AsyncWebsocketConsumer

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

        except json.JSONDecodeError:
            await self.send_error("Invalid message format")

    async def handle_user_message(self, data):
        """Process user message and generate AI response."""
        message = data.get("message", "").strip()
        print(f"==>> message: {message}")

        if not message:
            await self.send_error("Message cannot be empty")
            return

        # Show typing indicator
        await self.send(text_data=json.dumps({"type": "ai_typing", "is_typing": True}))

        ai_service = AIService(self.user)
        print(f"==>> ai_service: {ai_service}")

        response = await ai_service.process_query(message)
        print(f"==>> response: {response}")

        await self.send(json.dumps({"type": "ai_typing", "is_typing": False}))

        await self.send(json.dumps({"type": "ai_message", "message": response}))

    async def handle_typing_indicator(self, data):
        """Handle typing indicator from user."""
        is_typing = data.get("is_typing", False)

        # Broadcast typing status back to user
        await self.send(
            text_data=json.dumps({"type": "user_typing", "is_typing": is_typing})
        )

    async def send_error(self, error_message):
        """Send error message to WebSocket."""
        return f"error handling not implemented yet : {error_message}"
