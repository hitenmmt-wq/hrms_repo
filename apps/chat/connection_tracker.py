"""
WebSocket connection tracker for chat conversations.

Tracks active WebSocket connections to prevent duplicate notifications
when users are actively connected to chat conversations.
"""

from typing import Set

import redis
from django.conf import settings


class ChatConnectionTracker:
    """Redis-based connection tracker for chat WebSocket connections."""

    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, "REDIS_HOST", "127.0.0.1"),
                port=getattr(settings, "REDIS_PORT", 6379),
                db=getattr(settings, "REDIS_DB", 0),
                decode_responses=True,
            )
        except Exception:
            self.redis_client = None
            print("Redis not available, connection tracking disabled")

    def add_connection(self, user_id: int, conversation_id: int):
        """Add a user's connection to a conversation."""
        if not self.redis_client:
            return

        key = f"chat_connections:{user_id}"
        self.redis_client.sadd(key, str(conversation_id))
        self.redis_client.expire(key, 3600)  # Expire after 1 hour
        print(f"Added connection: User {user_id} -> Conversation {conversation_id}")

    def remove_connection(self, user_id: int, conversation_id: int):
        """Remove a user's connection from a conversation."""
        if not self.redis_client:
            return

        key = f"chat_connections:{user_id}"
        self.redis_client.srem(key, str(conversation_id))
        print(f"Removed connection: User {user_id} -> Conversation {conversation_id}")

    def is_connected(self, user_id: int, conversation_id: int) -> bool:
        """Check if user is connected to a specific conversation."""
        if not self.redis_client:
            return False

        key = f"chat_connections:{user_id}"
        connected = self.redis_client.sismember(key, str(conversation_id))
        print(
            f"Checking connection: User {user_id} -> Conversation {conversation_id}: {connected}"
        )
        return connected

    def get_user_connections(self, user_id: int) -> Set[int]:
        """Get all conversation IDs user is connected to."""
        if not self.redis_client:
            return set()

        key = f"chat_connections:{user_id}"
        connections = self.redis_client.smembers(key)
        return {int(conn_id) for conn_id in connections}

    def remove_user(self, user_id: int):
        """Remove all connections for a user."""
        if not self.redis_client:
            return

        key = f"chat_connections:{user_id}"
        self.redis_client.delete(key)
        print(f"Removed all connections for user {user_id}")


# Global instance
chat_tracker = ChatConnectionTracker()
