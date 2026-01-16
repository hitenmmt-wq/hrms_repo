from django.db import models

from apps.base.models import BaseModel
from apps.superadmin.models import Users

# Create your models here.


class ChatSession(BaseModel):
    """Chat sessions between users."""

    session_name = models.CharField(max_length=255, null=True, blank=True)
    participants = models.ManyToManyField(Users, related_name="chat_sessions")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.session_name or "Unnamed Session"
