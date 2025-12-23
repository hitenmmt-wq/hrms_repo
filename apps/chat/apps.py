from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = "apps.chat"

    def ready(self):
        import apps.notification.signals  # noqa: F401
