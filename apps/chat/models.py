from django.db import models
from apps.adminapp.models import Users
from apps.base.models import BaseModel

# Create your models here.


class Conversation(models.Model):
    CONVERSATION_TYPES = (
        ('private', 'private'),
        ('group', 'group'),
    )
    type = models.CharField(max_length=20, choices=CONVERSATION_TYPES)
    name = models.CharField(max_length=255, null=True, blank=True) 
    participants = models.ManyToManyField(Users, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.type}"
    


class Message(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="sender_user")
    text = models.TextField(null=True, blank=True)
    media = models.FileField(upload_to="chat_media/", null=True, blank=True) 
    msg_type = models.CharField(max_length=20, default="text") 
    
    def __str__(self):
        return f"{self.sender.email} - {self.conversation.name} "
    

class MessageStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="statuses")
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="user_status")
    status = models.CharField(max_length=20, default="sent")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.status}"
    