from django.urls import path

from apps.chat import views

urlpatterns = [
    path(
        "conversations/", views.ConversationListView.as_view(), name="conversation-list"
    ),
    path("remaining_users/", views.RemainingUsers.as_view(), name="remaining_users"),
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
    path(
        "group_profile_upload/",
        views.GroupProfileUploadView.as_view(),
        name="group-profile-upload",
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
    path(
        "messages/<int:message_id>/reactions/",
        views.MessageReactionView.as_view(),
        name="message-reactions",
    ),
    # E2E Encryption key exchange endpoints
    path(
        "keys/set_public_key/",
        views.SetPublicKeyView.as_view(),
        name="set-public-key",
    ),
    path(
        "keys/get_public_key/",
        views.GetPublicKeyView.as_view(),
        name="get-public-key",
    ),
    path(
        "keys/my_keys/",
        views.MyKeysView.as_view(),
        name="my-keys",
    ),
]
