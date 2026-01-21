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

            # Try localhost first, then try Docker host
            redis_hosts = [
                ("127.0.0.1", 6379),  # Local Redis
                ("host.docker.internal", 6379),  # Docker Redis on Windows/Mac
                ("redis", 6379),  # Docker DNS name
            ]

            redis_host = getattr(settings, "REDIS_HOST", "127.0.0.1")
            redis_port = getattr(settings, "REDIS_PORT", 6379)

            # Add configured host to the beginning of the list
            redis_hosts = [(redis_host, redis_port)] + redis_hosts

            self.redis_client = None
            last_error = None

            # Try each host until one works
            for host, port in redis_hosts:
                try:
                    client = redis.Redis(
                        host=host,
                        port=port,
                        db=getattr(settings, "REDIS_DB", 0),
                        decode_responses=True,
                        socket_connect_timeout=2,
                        socket_timeout=2,
                        retry_on_timeout=True,
                        health_check_interval=30,
                    )
                    client.ping()
                    self.redis_client = client
                    print(
                        f"✅ Redis connection established for chat tracker at {host}:{port}"
                    )
                    return
                except Exception as e:
                    last_error = e
                    continue

            # If no connection worked, set to None
            self.redis_client = None
            print(f"❌ Redis not available for chat tracker: {last_error}")
        except Exception as e:
            self.redis_client = None
            print(f"❌ Redis initialization error: {e}")

    def add_connection(
        self, user_id: int, conversation_id: int, is_visible: bool = True
    ):
        """Add a user's connection to a conversation."""
        if not self.redis_client:
            return

        try:
            key = f"chat_connections:{user_id}"
            self.redis_client.sadd(key, str(conversation_id))
            self.redis_client.expire(key, 3600)  # Expire after 1 hour

            visibility_key = f"chat_visible:{user_id}:{conversation_id}"
            self.redis_client.set(visibility_key, "1" if is_visible else "0", ex=3600)

            print(
                f"Added connection: User {user_id} -> Conversation {conversation_id} (visible: {is_visible})"
            )
        except Exception as e:
            print(f"Redis connection error in add_connection: {e}")

    def remove_connection(self, user_id: int, conversation_id: int):
        """Remove a user's connection from a conversation."""
        if not self.redis_client:
            return

        try:
            key = f"chat_connections:{user_id}"
            self.redis_client.srem(key, str(conversation_id))

            # Remove visibility tracking
            visibility_key = f"chat_visible:{user_id}:{conversation_id}"
            self.redis_client.delete(visibility_key)

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

    def is_tab_visible(self, user_id: int, conversation_id: int) -> bool:
        """Check if user's tab is visible for a specific conversation."""
        if not self.redis_client:
            return False

        try:
            visibility_key = f"chat_visible:{user_id}:{conversation_id}"
            visible = self.redis_client.get(visibility_key)
            return visible == "1" if visible else False
        except Exception as e:
            print(f"Redis connection error in is_tab_visible: {e}")
            return False

    def set_tab_visibility(self, user_id: int, conversation_id: int, is_visible: bool):
        """Update tab visibility status."""
        if not self.redis_client:
            return

        try:
            visibility_key = f"chat_visible:{user_id}:{conversation_id}"
            self.redis_client.set(visibility_key, "1" if is_visible else "0", ex=3600)
            print(
                f"Updated visibility: User {user_id} -> Conversation {conversation_id}: {is_visible}"
            )
        except Exception as e:
            print(f"Redis connection error in set_tab_visibility: {e}")

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
