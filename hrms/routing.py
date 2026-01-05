from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from apps.chat.middleware import JwtAuthMiddleware
from apps.chat.routing import websocket_urlpatterns as chat_urlpatterns
from apps.notification.consumers import NotificationConsumer

# Combine all WebSocket URL patterns (Chat, Notification)
websocket_urlpatterns = chat_urlpatterns + [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JwtAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
