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
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Test the connection
            self.redis_client.ping()
            print("Redis connection established for chat tracker")
        except Exception as e:
            self.redis_client = None
            print(f"Redis not available for chat tracker: {e}")

    def add_connection(self, user_id: int, conversation_id: int):
        """Add a user's connection to a conversation."""
        if not self.redis_client:
            return

        try:
            key = f"chat_connections:{user_id}"
            self.redis_client.sadd(key, str(conversation_id))
            self.redis_client.expire(key, 3600)  # Expire after 1 hour
            print(f"Added connection: User {user_id} -> Conversation {conversation_id}")
        except Exception as e:
            print(f"Redis connection error in add_connection: {e}")

    def remove_connection(self, user_id: int, conversation_id: int):
        """Remove a user's connection from a conversation."""
        if not self.redis_client:
            return

        try:
            key = f"chat_connections:{user_id}"
            self.redis_client.srem(key, str(conversation_id))
            print(
                f"Removed connection: User {user_id} -> Conversation {conversation_id}"
            )
        except Exception as e:
            print(f"Redis connection error in remove_connection: {e}")

    def is_connected(self, user_id: int, conversation_id: int) -> bool:
        """Check if user is connected to a specific conversation."""
        if not self.redis_client:
            return False

        try:
            key = f"chat_connections:{user_id}"
            connected = self.redis_client.sismember(key, str(conversation_id))
            print(
                f"Checking connection: User {user_id} -> Conversation {conversation_id}: {connected}"
            )
            return connected
        except Exception as e:
            print(f"Redis connection error in is_connected: {e}")
            return False

    def get_user_connections(self, user_id: int) -> Set[int]:
        """Get all conversation IDs user is connected to."""
        if not self.redis_client:
            return set()

        try:
            key = f"chat_connections:{user_id}"
            connections = self.redis_client.smembers(key)
            return {int(conn_id) for conn_id in connections}
        except Exception as e:
            print(f"Redis connection error in get_user_connections: {e}")
            return set()

    def remove_user(self, user_id: int):
        """Remove all connections for a user."""
        if not self.redis_client:
            return

        try:
            key = f"chat_connections:{user_id}"
            self.redis_client.delete(key)
            print(f"Removed all connections for user {user_id}")
        except Exception as e:
            print(f"Redis connection error in remove_user: {e}")


# Global instance
chat_tracker = ChatConnectionTracker()
