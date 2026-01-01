from django.urls import path

from apps.chat import views

urlpatterns = [
    path(
        "conversations/", views.ConversationListView.as_view(), name="conversation-list"
    ),
    path(
        "conversations/create/",
        views.CreateConversationView.as_view(),
        name="conversation-create",
    ),
    path(
        "conversations/<int:pk>/delete/",
        views.ConversationDeleteView.as_view(),
        name="conversation-delete",
    ),
    path("upload/", views.FileUploadView.as_view(), name="chat-file-upload"),
    path(
        "get_conversation_messages/<int:conversation>/",
        views.ConversationMessageView.as_view(),
        name="get_conversation_messages",
    ),
    path(
        "message_read/<int:message_id>/",
        views.MessageReadView.as_view(),
        name="message_read",
    ),
]
