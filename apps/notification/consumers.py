import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        print(f"==>> user: {user}")
        logger.info(f"NotificationConsumer connect - user from scope: {user}")

        # If not authenticated via middleware, try query param
        if not user or not user.is_authenticated:
            query_string = self.scope.get("query_string", b"").decode()
            token = None
            if "token=" in query_string:
                token = query_string.split("token=")[1].split("&")[0]
            if token:
                try:
                    access_token = AccessToken(token)
                    user_id = access_token.payload.get("user_id")
                    user = await User.objects.aget(id=user_id)
                    self.scope["user"] = user
                except Exception as e:
                    print(f"Token error: {e}")
                    await self.close()
                    return
            else:
                await self.close()
                return

        self.user = user
        self.room_group_name = f"notifications_{self.user.id}"
        try:
            if self.channel_layer:
                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )
                logger.info(f"Successfully added to group: {self.room_group_name}")

            await self.accept()
            logger.info("Connection established successfully - waiting for messages")
        except Exception as e:
            logger.error(f"Error in group_add or accept: {e}")
            await self.close()
            return

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnecting with code: {close_code}")
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        logger.info(
            f"WebSocket disconnected for user: {getattr(self, 'user', 'unknown')}"
        )

    async def notification_message(self, event):
        logger.info(f"Sending notification message: {event['payload']}")
        await self.send_json(event["payload"])
