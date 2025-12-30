from django.urls import path

from apps.chat.views import (
    ConversationDeleteView,
    ConversationListView,
    CreateConversationView,
    FileUploadView,
)

urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path(
        "conversations/create/",
        CreateConversationView.as_view(),
        name="conversation-create",
    ),
    path(
        "conversations/<int:pk>/delete/",
        ConversationDeleteView.as_view(),
        name="conversation-delete",
    ),
    path("upload/", FileUploadView.as_view(), name="chat-file-upload"),
]
