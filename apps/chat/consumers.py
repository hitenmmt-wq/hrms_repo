"""
WebSocket consumer for real-time chat functionality.

Handles WebSocket connections, message sending/receiving, typing indicators,
read receipts, message reactions, and real-time notifications for the HRMS chat system.
"""

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.connection_tracker import chat_tracker
from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus
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

        # Track this connection
        chat_tracker.add_connection(self.user.id, self.conversation_id)
        # Debug: Show all user connections after adding
        user_connections = chat_tracker.get_user_connections(self.user.id)
        print(f"📱 User {self.user.email} now has connections: {user_connections}")

        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection and cleanup."""
        if hasattr(self, "room_group_name") and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

        # Remove connection tracking
        if hasattr(self, "user") and hasattr(self, "conversation_id"):
            chat_tracker.remove_connection(self.user.id, self.conversation_id)
            user_connections = chat_tracker.get_user_connections(self.user.id)
            print(f"==>> user_connections: {user_connections}")

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

        message_data = await self.create_message_with_data(
            self.conversation_id, self.user.id, text, msg_type, reply_to
        )
        if message_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "payload": {
                        "type": "new_message",
                        "message": message_data,
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

    async def handle_add_reaction(self, content):
        """Handle adding emoji reactions to messages."""
        message_id = content.get("message_id")
        emoji = content.get("emoji")

        if message_id and emoji:
            reaction_data = await self.add_reaction(message_id, self.user.id, emoji)
            if reaction_data:
                payload = {
                    "type": "reaction_added",
                    "message_id": message_id,
                    "reaction": reaction_data,
                }
                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "chat.message", "payload": payload}
                )

    async def handle_remove_reaction(self, content):
        """Handle removing emoji reactions from messages."""
        message_id = content.get("message_id")
        emoji = content.get("emoji")

        if message_id and emoji:
            success = await self.remove_reaction(message_id, self.user.id, emoji)
            if success:
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
    def create_message_with_data(
        self, conversation_id, user_id, text, msg_type, reply_to
    ):
        """Create new message and return simple data dict."""
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
            return {
                "id": message.id,
                "text": message.text,
                "msg_type": message.msg_type,
                "sender": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "created_at": message.created_at.isoformat(),
                "reply_to": reply_message.id if reply_message else None,
            }
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
                message=message, user=user, defaults={"status": status}
            )
        except (Message.DoesNotExist, Users.DoesNotExist):
            pass

    @database_sync_to_async
    def add_reaction(self, message_id, user_id, emoji):
        """Add emoji reaction to message."""
        try:
            message = Message.objects.get(id=message_id)
            user = Users.objects.get(id=user_id)

            reaction, created = MessageReaction.objects.get_or_create(
                message=message, user=user, emoji=emoji, defaults={"is_deleted": False}
            )

            if not created and reaction.is_deleted:
                reaction.is_deleted = False
                reaction.save()
                created = True

            if created:
                return {
                    "id": reaction.id,
                    "emoji": reaction.emoji,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "created_at": reaction.created_at.isoformat(),
                }
            return None
        except (Message.DoesNotExist, Users.DoesNotExist):
            return None

    @database_sync_to_async
    def remove_reaction(self, message_id, user_id, emoji):
        """Remove emoji reaction from message."""
        try:
            reaction = MessageReaction.objects.get(
                message_id=message_id, user_id=user_id, emoji=emoji, is_deleted=False
            )
            reaction.is_deleted = True
            reaction.save()
            return True
        except MessageReaction.DoesNotExist:
            return False

    @database_sync_to_async
    def get_conversation_participants(self, conversation_id):
        """Get list of participant IDs for a conversation."""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return list(conversation.participants.values_list("id", flat=True))
        except Conversation.DoesNotExist:
            return []

    async def chat_message(self, event):
        """Send message to WebSocket client."""
        await self.send_json(event["payload"])

    async def notification_message(self, event):
        """Send notification to WebSocket client."""
        await self.send_json(event["payload"])
