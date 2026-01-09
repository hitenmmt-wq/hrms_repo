"""
WebSocket connection tracker for chat conversations.

Tracks active WebSocket connections to prevent duplicate notifications
when users are actively connected to chat conversations.
"""

from typing import Dict, Set


class ChatConnectionTracker:
    """Singleton class to track active chat WebSocket connections."""

    _instance = None
    _connections: Dict[int, Set[int]] = (
        {}
    )  # {user_id: {conversation_id1, conversation_id2, ...}}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def add_connection(self, user_id: int, conversation_id: int):
        """Add a user's connection to a conversation."""
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(conversation_id)

    def remove_connection(self, user_id: int, conversation_id: int):
        """Remove a user's connection from a conversation."""
        if user_id in self._connections:
            self._connections[user_id].discard(conversation_id)
            if not self._connections[user_id]:
                del self._connections[user_id]

    def is_connected(self, user_id: int, conversation_id: int) -> bool:
        """Check if user is connected to a specific conversation."""
        return (
            user_id in self._connections
            and conversation_id in self._connections[user_id]
        )

    def get_user_connections(self, user_id: int) -> Set[int]:
        """Get all conversation IDs user is connected to."""
        return self._connections.get(user_id, set())

    def remove_user(self, user_id: int):
        """Remove all connections for a user."""
        self._connections.pop(user_id, None)


# Global instance
chat_tracker = ChatConnectionTracker()
