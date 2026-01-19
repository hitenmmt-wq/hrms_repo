"""
WebSocket consumer for real-time chat functionality.
"""

from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils import timezone

from apps.chat.connection_tracker import chat_tracker
from apps.chat.models import Conversation, Message, MessageReaction, MessageStatus
from apps.notification.models import Notification, NotificationType
from apps.superadmin.models import Users


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for handling real-time chat operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_tab_visible = True

    async def connect(self):
        """Handle WebSocket connection."""
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user

        # Join global user group
        self.global_user_group = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.global_user_group, self.channel_name)

        # Join specific conversation if provided
        conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")
        if conversation_id:
            self.conversation_id = conversation_id
            is_participant = await self.is_participant(conversation_id, user.id)
            if is_participant:
                self.room_group_name = f"chat_{conversation_id}"
                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )
                chat_tracker.add_connection(self.user.id, conversation_id)

        await self.accept()
        await self.send_missed_messages()
        await self.send_unread_counts()

        # Mark messages as read if in specific conversation
        if hasattr(self, "conversation_id"):
            await self.mark_and_broadcast_read_messages()
            await self.channel_layer.group_send(
                self.global_user_group, {"type": "global.unread_update"}
            )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        if hasattr(self, "global_user_group"):
            await self.channel_layer.group_discard(
                self.global_user_group, self.channel_name
            )
        if hasattr(self, "user") and hasattr(self, "conversation_id"):
            chat_tracker.remove_connection(self.user.id, self.conversation_id)

    async def receive_json(self, content, **kwargs):
        """Route incoming WebSocket messages."""
        event = content.get("type")
        handlers = {
            "send_message": self.handle_send_message,
            "typing_start": self.handle_start_typing,
            "typing_stop": self.handle_stop_typing,
            "tab_visible": self.handle_tab_visibility,
            "add_reaction": self.handle_add_reaction,
            "remove_reaction": self.handle_remove_reaction,
            "get_messages": self.handle_get_messages,
            # "mark_read": self.handle_mark_read(content),
            "heartbeat": lambda _: self.send_json({"type": "heartbeat_ack"}),
        }

        handler = handlers.get(event)
        if handler:
            await handler(content)

    async def handle_send_message(self, content):
        print(f"==>> content: {content}")
        """Handle sending new messages and broadcasting to conversation participants."""
        text = content.get("text", "")
        msg_type = content.get("msg_type", "text")
        reply_to = content.get("reply_to")
        conversation_id = content.get("conversation_id")

        message_data = await self.create_message_with_data(
            conversation_id, self.user.id, text, msg_type, reply_to
        )
        if message_data:
            if hasattr(self, "room_group_name"):
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

    async def handle_start_typing(self, content):
        print(f"==>> content: {content}")
        """Broadcast typing start to all participants."""
        await self.broadcast_typing(content)

    async def handle_stop_typing(self, content):
        print(f"==>> content: {content}")
        """Broadcast typing stop to all participants."""
        await self.broadcast_typing(content)

    async def broadcast_typing(self, data):
        """Broadcast typing indicator to conversation and global groups."""
        payload = {
            "type": data.get("type"),
            "conversation_id": data.get("conversation_id"),
            "user": {
                "id": self.user.id,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
        }

        # Send to conversation group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "payload": payload,
                    "sender_id": self.user.id,
                },
            )

        # Send to participants' global groups
        participants = await self.get_conversation_participants(
            data.get("conversation_id")
        )
        for participant_id in participants:
            if participant_id != self.user.id:
                await self.channel_layer.group_send(
                    f"user_{participant_id}",
                    {
                        "type": "global.typing",
                        "payload": payload,
                        "sender_id": self.user.id,
                    },
                )

    async def mark_and_broadcast_read_messages(self):
        """Mark messages as read and broadcast to participants."""
        read_message_ids = await self.mark_all_messages_read(
            self.conversation_id, self.user.id
        )
        await self.notify_message_read(read_message_ids)
        if not read_message_ids:
            return

        messages = await self.get_messages_for_read_receipt(read_message_ids)

        for msg in messages:
            await self.channel_layer.group_send(
                f"user_{msg['sender_id']}",
                {
                    "type": "global.message_read",
                    "payload": {
                        "type": "message_read",
                        "conversation_id": msg["conversation_id"],
                        "message_id": msg["id"],
                        "reader": {
                            "id": self.user.id,
                            "first_name": self.user.first_name,
                            "last_name": self.user.last_name,
                        },
                    },
                },
            )

            # Send to conversation group
            # if hasattr(self, 'room_group_name'):
            #     await self.channel_layer.group_send(
            #         self.room_group_name, {"type": "chat.message", "payload": payload}
            #     )

            # # Send to participants' global groups
            # participants = await self.get_conversation_participants(self.conversation_id)
            # for participant_id in participants:
            #     if participant_id != self.user.id:
            #         await self.channel_layer.group_send(
            #             f"user_{participant_id}",
            #             {"type": "global.read_receipt", "payload": payload}
            #         )

    async def notify_message_read(self, message_ids):
        """Notify senders that their messages were read"""
        if not message_ids:
            return

        messages = await self.get_messages_with_senders(message_ids)

        for msg in messages:
            await self.channel_layer.group_send(
                f"user_{msg.sender_id}",
                {
                    "type": "global.message_read",
                    "payload": {
                        "type": "message_read",
                        "conversation_id": msg.conversation_id,
                        "message_id": msg.id,
                        "reader": {
                            "id": self.user.id,
                            "first_name": self.user.first_name,
                            "last_name": self.user.last_name,
                        },
                        "read_at": timezone.now().isoformat(),
                    },
                },
            )

    async def handle_tab_visibility(self, content):
        """Handle tab visibility changes."""
        self.is_tab_visible = content.get("visible", True)
        if self.is_tab_visible and hasattr(self, "conversation_id"):
            await self.mark_and_broadcast_read_messages()

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

    async def global_unread_update(self, event):
        await self.send_unread_counts()

    @database_sync_to_async
    def get_messages_for_read_receipt(self, message_ids):
        """
        Returns minimal data required to notify senders
        """
        return list(
            Message.objects.filter(id__in=message_ids).values(
                "id", "sender_id", "conversation_id"
            )
        )

    @database_sync_to_async
    def get_messages_with_senders(self, message_ids):
        return list(
            Message.objects.filter(id__in=message_ids).only(
                "id", "conversation_id", "sender_id"
            )
        )

    @database_sync_to_async
    def get_unread_counts(self, user_id):
        """Get count of unread messages for user across all conversations."""
        qs = (
            MessageStatus.objects.filter(
                user_id=user_id, status__in=["sent", "delivered"]
            )
            .values("message__conversation_id")
            .annotate(count=Count("id"))
        )

        by_conversation = {
            str(row["message__conversation_id"]): {
                "conversation_id": str(row["message__conversation_id"]),
                "count": row["count"],
            }
            for row in qs
        }
        print(f"==>> by_conversation: {by_conversation}")

        total = sum(item["count"] for item in by_conversation.values())
        print(f"==>> total: {total}")

        return {"total": total, "by_conversation": by_conversation}

    @database_sync_to_async
    def mark_all_messages_read(self, conversation_id, user_id):
        """Mark all unread messages in conversation as read when user opens chat."""
        # Get all messages not sent by this user that aren't already read
        unread_statuses = MessageStatus.objects.filter(
            user_id=user_id,
            message__conversation_id=conversation_id,
            status__in=["sent", "delivered"],
        ).exclude(message__sender_id=user_id)

        # Get message IDs before updating
        message_ids = list(unread_statuses.values_list("message_id", flat=True))

        # Update to read
        unread_statuses.update(status="read")

        return message_ids

    @database_sync_to_async
    def mark_single_message_read(self, message_id, user_id):
        """Mark a single message as read."""
        try:
            MessageStatus.objects.filter(
                message_id=message_id, user_id=user_id
            ).exclude(message__sender_id=user_id).update(status="read")
        except Exception as e:
            print(f"Error marking message as read: {e}")

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
                is_connected = chat_tracker.is_connected(
                    participant.id, conversation_id
                )
                is_visible = chat_tracker.is_tab_visible(
                    participant.id, conversation_id
                )

                if is_connected and is_visible:
                    initial_status = "read"
                elif is_connected:
                    initial_status = "delivered"
                else:
                    initial_status = "sent"

                MessageStatus.objects.create(
                    message=message,
                    user=participant,
                    status=initial_status,
                )

                async_to_sync(self.channel_layer.group_send)(
                    f"user_{participant.id}", {"type": "global.unread_update"}
                )

                if not (is_connected and is_visible):
                    self._create_chat_notification(message, participant)

                    async_to_sync(self.channel_layer.group_send)(
                        f"user_{participant.id}",
                        {
                            "type": "global.message",
                            "payload": {
                                "type": "new_message",
                                "message_id": message.id,
                                "conversation_id": conversation_id,
                                "sender": {
                                    "id": user.id,
                                    "email": user.email,
                                    "first_name": user.first_name,
                                    "last_name": user.last_name,
                                },
                                "message": {
                                    "id": message.id,
                                    "text": text,
                                    "msg_type": msg_type,
                                    "created_at": message.created_at.isoformat(),
                                },
                                "timestamp": message.created_at.isoformat(),
                            },
                        },
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

    def _create_chat_notification(self, message, recipient):
        """Create notification for new chat message."""
        try:
            notification_type, _ = NotificationType.objects.get_or_create(
                code="new_message", defaults={"name": "New Message"}
            )

            content_type = ContentType.objects.get_for_model(Message)

            Notification.objects.create(
                recipient=recipient,
                actor=message.sender,
                notification_type=notification_type,
                content_type=content_type,
                object_id=message.id,
                title=f"New message from {message.sender.first_name} {message.sender.last_name}",
                message=message.text[:100] if message.text else "Sent a file",
                is_read=False,
            )
        except Exception as e:
            print(f"Error creating notification: {e}")

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

    # WebSocket event handlers
    async def global_message_read(self, event):
        await self.send_json(event["payload"])

    async def global_typing(self, event):
        print(f"==>> event-------------------: {event}")
        if event.get("sender_id") != self.user.id:
            await self.send_json(event["payload"])

    async def global_read_receipt(self, event):
        if event["payload"]["user_id"] != self.user.id:
            await self.send_json(event["payload"])

    async def global_message(self, event):
        await self.send_json(event["payload"])

    # async def typing_indicator(self, event):
    #     print(f"==>> event=====================: {event}")
    #     if event.get("sender_id") != self.user.id:
    #         await self.send_json(event["payload"])

    async def chat_message(self, event):
        payload = event["payload"]
        await self.send_json(payload)

        # Auto-mark as read if tab visible
        if (
            payload.get("type") == "new_message"
            and self.is_tab_visible
            and payload.get("message", {}).get("sender", {}).get("id") != self.user.id
        ):
            message_id = payload.get("message", {}).get("id")
            if message_id:
                await self.mark_single_message_read(message_id, self.user.id)

    async def read_receipt(self, event):
        if event["payload"]["user_id"] != self.user.id:
            await self.send_json(event["payload"])

    async def send_missed_messages(self):
        """Send missed messages to user."""
        try:
            missed_messages = await self.get_unread_messages(self.user.id)
            for message in missed_messages:
                await self.send_json(
                    {
                        "type": "missed_message",
                        "message_id": message.id,
                        "conversation_id": message.conversation_id,
                        "sender": message.sender.email,
                        "content": message.text,
                        "timestamp": message.created_at.isoformat(),
                    }
                )
        except Exception as e:
            print(f"Failed to load missed messages: {e}")

    async def send_unread_counts(self):
        data = await self.get_unread_counts(self.user.id)
        await self.send_json(
            {
                "type": "unread_counts",
                "total_unread": data["total"],
                "by_conversation": data["by_conversation"],
            }
        )

    async def handle_get_messages(self, content):
        """Handle message history requests."""
        try:
            messages = await self.get_conversation_messages(
                self.conversation_id,
                self.user.id,
                content.get("last_message_id"),
                content.get("limit", 50),
            )

            await self.send_json(
                {
                    "type": "messages",
                    "conversation_id": self.conversation_id,
                    "messages": [
                        {
                            "id": msg.id,
                            "sender": msg.sender.email,
                            "text": msg.text,
                            "timestamp": msg.created_at.isoformat(),
                        }
                        for msg in messages
                    ],
                }
            )
        except Exception as e:
            await self.send_json(
                {"type": "error", "message": f"Failed to get messages: {str(e)}"}
            )

    @database_sync_to_async
    def get_unread_messages(self, user_id, since_minutes=60):
        """Get unread messages for user from last hour."""
        user_conversations = Conversation.objects.filter(participants=user_id)

        since_time = timezone.now() - timedelta(minutes=since_minutes)

        messages = (
            Message.objects.filter(
                conversation__in=user_conversations,
                created_at__gt=since_time,
                statuses__user_id=user_id,
                statuses__status__in=["sent", "delivered"],
            )
            .exclude(sender_id=user_id)
            .select_related("sender")
            .order_by("-created_at")[:20]
        )

        return list(messages)

    @database_sync_to_async
    def get_conversation_messages(
        self, conversation_id, user_id, last_message_id=None, limit=50
    ):
        """Get messages for a conversation with pagination."""
        # Verify user has access to conversation
        conversation = Conversation.objects.filter(
            id=conversation_id, participants=user_id
        ).first()

        if not conversation:
            return []

        query = Message.objects.filter(conversation_id=conversation_id)

        if last_message_id:
            query = query.filter(id__gt=last_message_id)

        messages = query.select_related("sender").order_by("created_at")[:limit]

        return list(messages)
