from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus
from apps.chat.serializers import MessageSerializer
from apps.superadmin.models import Users


class ChatConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        try:
            self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        except (KeyError, TypeError):
            await self.close()
            return

        # Verify user is participant in conversation
        if not await self.is_participant(self.conversation_id, user.id):
            await self.close()
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.mark_messages_delivered(self.conversation_id, self.user.id)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name") and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        event = content.get("type")
        print(f"==>> event: {event}")

        if event == "send_message":
            await self.handle_send_message(content)
        elif event == "typing":
            await self.handle_typing(content)
        elif event == "mark_read":
            await self.handle_mark_read(content)
        elif event == "status_update":
            await self.handle_status_update(content)
        elif event == "add_reaction":
            await self.handle_add_reaction(content)
        elif event == "remove_reaction":
            await self.handle_remove_reaction(content)

    async def handle_send_message(self, content):
        text = content.get("text", "")
        msg_type = content.get("msg_type", "text")
        reply_to = content.get("reply_to")

        message = await self.create_message(
            self.conversation_id, self.user.id, text, msg_type, reply_to
        )

        if message:
            serializer = MessageSerializer(message, context={"request": None})
            print(f"==>> serializer: {serializer}")

            notification_payload = {
                "type": "new_notification",
                "notification": {
                    "title": f"New message from {self.user.email}",
                    "message": (text or "")[:100],
                    "type": "chat_message",
                },
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "notification.message", "payload": notification_payload},
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "payload": {
                        "type": "new_message",
                        "message": MessageSerializer(message).data,
                    },
                },
            )

    async def handle_typing(self, content):
        payload = {"type": "typing", "user_id": self.user.id}
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "payload": payload}
        )

    async def handle_mark_read(self, content):
        message_id = content.get("message_id")
        if message_id:
            await self.mark_message_read(message_id, self.user.id)

    async def handle_status_update(self, content):
        message_id = content.get("message_id")
        status = content.get("status")
        if message_id and status:
            await self.update_message_status(message_id, self.user.id, status)

    @database_sync_to_async
    def mark_messages_delivered(self, conversation_id, user_id):
        MessageStatus.objects.filter(
            user_id=user_id, message__conversation_id=conversation_id, status="sent"
        ).update(status="delivered")

    @database_sync_to_async
    def is_participant(self, conversation_id, user_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.filter(id=user_id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, conversation_id, user_id, text, msg_type, reply_to):
        try:
            conversation = Conversation.objects.get(id=conversation_id)

            user = Users.objects.get(id=user_id)

            reply_message = None
            if reply_to:
                try:
                    reply_message = Message.objects.get(id=reply_to)
                except Message.DoesNotExist:
                    pass

            message = Message.objects.create(
                conversation=conversation,
                sender=user,
                text=text,
                msg_type=msg_type,
                reply_to=reply_message,
            )
            participants = conversation.participants.exclude(id=user.id)
            for participant in participants:
                MessageStatus.objects.create(
                    message=message,
                    user=participant,
                    status="sent",
                )
            return message
        except (Conversation.DoesNotExist, Users.DoesNotExist):
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id, user_id):
        try:
            message = Message.objects.get(id=message_id)

            user = Users.objects.get(id=user_id)

            MessageStatus.objects.update_or_create(
                message=message, user=user, defaults={"status": "read"}
            )
        except (Message.DoesNotExist, Users.DoesNotExist):
            pass

    @database_sync_to_async
    def update_message_status(self, message_id, user_id, status):
        try:
            message = Message.objects.get(id=message_id)
            user = Users.objects.get(id=user_id)

            MessageStatus.objects.update_or_create(
                message=message,
                user=user,
                defaults={"status": status},
            )
        except (Message.DoesNotExist, Users.DoesNotExist):
            pass

    async def handle_add_reaction(self, content):
        message_id = content.get("message_id")
        emoji = content.get("emoji")

        if message_id and emoji:
            reaction = await self.add_reaction(message_id, self.user.id, emoji)
            if reaction:
                payload = {
                    "type": "reaction_added",
                    "message_id": message_id,
                    "user_id": self.user.id,
                    "emoji": emoji,
                }
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "chat.message", "payload": payload}
                )

    async def handle_remove_reaction(self, content):
        message_id = content.get("message_id")
        emoji = content.get("emoji")

        if message_id and emoji:
            removed = await self.remove_reaction(message_id, self.user.id, emoji)
            if removed:
                payload = {
                    "type": "reaction_removed",
                    "message_id": message_id,
                    "user_id": self.user.id,
                    "emoji": emoji,
                }
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "chat.message", "payload": payload}
                )

    @database_sync_to_async
    def add_reaction(self, message_id, user_id, emoji):
        try:
            message = Message.objects.get(id=message_id)

            user = Users.objects.get(id=user_id)

            reaction, created = MessageReaction.objects.get_or_create(
                message=message, user=user, emoji=emoji
            )
            return reaction
        except (Message.DoesNotExist, Users.DoesNotExist):
            return None

    @database_sync_to_async
    def remove_reaction(self, message_id, user_id, emoji):
        try:
            message = Message.objects.get(id=message_id)

            user = Users.objects.get(id=user_id)

            deleted_count, _ = MessageReaction.objects.filter(
                message=message, user=user, emoji=emoji
            ).delete()
            return deleted_count > 0
        except (Message.DoesNotExist, Users.DoesNotExist):
            return False

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def notification_message(self, event):
        await self.send_json(event["payload"])
