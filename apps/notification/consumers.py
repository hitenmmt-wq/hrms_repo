from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        print(f"==>> user: {user}")

        # If not authenticated via middleware, try query param
        if not user or not user.is_authenticated:
            query_string = self.scope.get("query_string", b"").decode()
            print(f"==>> query_string: {query_string}")
            token = None
            if "token=" in query_string:
                token = query_string.split("token=")[1].split("&")[0]
                print(f"==>> token: {token}")
            if token:
                try:
                    access_token = AccessToken(token)
                    print(f"==>> access_token: {access_token}")
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
        print(f"==>> self.room_group_name: {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def notification_message(self, event):
        await self.send_json(event["payload"])
