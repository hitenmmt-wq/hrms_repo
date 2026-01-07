"""
JWT authentication middleware for WebSocket connections.

Handles JWT token authentication for Django Channels WebSocket connections,
extracting tokens from query parameters and setting user context for chat functionality.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from apps.superadmin.models import Users


class JwtAuthMiddleware:
    """Middleware for authenticating WebSocket connections using JWT tokens."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        """Process WebSocket connection and authenticate user via JWT token."""
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token")

        if token:
            try:
                access_token = AccessToken(token[0])
                user_id = int(access_token["user_id"])
                user = await self.get_user(user_id)
                scope["user"] = user if user else AnonymousUser()
            except Exception as e:
                print(f"JWT auth error: {e}")
                scope["user"] = AnonymousUser()
        else:
            print("No token provided")
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        """Retrieve active user by ID from database asynchronously."""
        try:
            user = Users.objects.get(id=user_id)
            print(f"Found user via ORM: {user} (email: {user.email})")
            return user
        except Users.DoesNotExist:
            print(f"User {user_id} not found via ORM")
            return None
        except Exception as e:
            print(f"Database error: {e}")
            import traceback

            traceback.print_exc()
            return None
