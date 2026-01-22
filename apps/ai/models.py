from django.db import models

from apps.base.models import BaseModel
from apps.superadmin.models import Users


class AIConversation(BaseModel):
    """AI conversation sessions with users."""

    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="ai_conversations"
    )
    session_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    context_data = models.JSONField(
        default=dict, blank=True
    )  # Store conversation context

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["session_id"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title or 'AI Chat'}"


class AIMessage(BaseModel):
    """Individual messages in AI conversations."""

    MESSAGE_TYPES = [
        ("user", "User Message"),
        ("ai", "AI Response"),
        ("system", "System Message"),
    ]

    conversation = models.ForeignKey(
        AIConversation, on_delete=models.CASCADE, related_name="messages"
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    metadata = models.JSONField(
        default=dict, blank=True
    )  # Store query intent, data sources, etc.
    response_time = models.FloatField(
        null=True, blank=True
    )  # AI response time in seconds

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["message_type"]),
        ]

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class AIQueryLog(BaseModel):
    """Log AI queries for analytics and improvement."""

    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="ai_queries")
    query = models.TextField()
    intent = models.CharField(max_length=100, null=True, blank=True)
    data_accessed = models.JSONField(
        default=list, blank=True
    )  # Track what data was accessed
    response_quality = models.IntegerField(null=True, blank=True)  # User rating 1-5
    processing_time = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["intent"]),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.query[:30]}..."
