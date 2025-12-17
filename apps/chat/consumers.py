from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        event = content.get("type")

        if event == "send_message":
            await self.handle_send_message(content)
        elif event == "typing":
            await self.handle_typing(content)
        elif event == "mark_read":
            await self.handle_mark_read(content)
        elif event == "status_update":
            await self.handle_status_update(content)

    async def handle_send_message(self, content):
        text = content.get("text")
        msg_type = content.get("msg_type", "text")
        reply_to = content.get("reply_to")

        message = await self.create_message(
            self.conversation_id, self.user.id, text, msg_type, reply_to
        )
        serializer = MessageSerializer(message, context={"request": None})

        payload = {
            "type": "new_message",
            "message": serializer.data,
        }
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "payload": payload}
        )

    async def handle_typing(self, content):
        payload = {"type": "typing", "user_id": self.user.id}
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "payload": payload}
        )

    async def handle_mark_read(self, content):
        message_id = content.get("message_id")
        await self.mark_message_read(message_id, self.user.id)
