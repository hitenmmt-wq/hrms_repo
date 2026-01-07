"""
WebSocket consumer for real-time chat functionality.

Handles WebSocket connections, message sending/receiving, typing indicators,
read receipts, message reactions, and real-time notifications for the HRMS chat system.
"""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus
from apps.chat.serializers import MessageSerializer
from apps.superadmin.models import Users


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for handling real-time chat operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None

    async def connect(self):
        """Handle WebSocket connection with user authentication and conversation verification."""
        user = self.scope.get("user")
        print(f"==>> user: {user}")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user
        try:
            self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        except (KeyError, TypeError) as e:
            print(f"==>> Connection rejected: Invalid conversation ID - {e}")
            await self.close(code=4002)
            return

        # Verify user is participant in conversation
        is_participant = await self.is_participant(self.conversation_id, user.id)
        if not is_participant:
            await self.close(code=4003)
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.mark_messages_delivered(self.conversation_id, self.user.id)
        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection and cleanup."""
        if hasattr(self, "room_group_name") and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        """Route incoming WebSocket messages to appropriate handlers."""
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
        """Handle sending new messages and broadcasting to conversation participants."""
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
        """Handle typing indicator broadcasts to conversation participants."""
        payload = {"type": "typing", "user_id": self.user.id}
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "payload": payload}
        )

    async def handle_mark_read(self, content):
        """Handle marking messages as read by the user."""
        message_id = content.get("message_id")
        if message_id:
            await self.mark_message_read(message_id, self.user.id)

    async def handle_status_update(self, content):
        """Handle updating message delivery status."""
        message_id = content.get("message_id")
        status = content.get("status")
        if message_id and status:
            await self.update_message_status(message_id, self.user.id, status)

    @database_sync_to_async
    def mark_messages_delivered(self, conversation_id, user_id):
        """Mark all sent messages in conversation as delivered for the user."""
        MessageStatus.objects.filter(
            user_id=user_id, message__conversation_id=conversation_id, status="sent"
        ).update(status="delivered")

    @database_sync_to_async
    def is_participant(self, conversation_id, user_id):
        """Check if user is a participant in the conversation."""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.filter(id=user_id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, conversation_id, user_id, text, msg_type, reply_to):
        """Create new message and initialize status for all participants."""
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
        """Mark specific message as read by the user."""
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
        """Update message status for specific user."""
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
        """Handle adding emoji reactions to messages."""
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
        """Handle removing emoji reactions from messages."""
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
        """Add emoji reaction to message."""
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
        """Remove emoji reaction from message."""
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
