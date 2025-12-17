from django.contrib import admin

from apps.chat import models

# Register your models here.

admin.site.register(models.Conversation)
admin.site.register(models.Message)
admin.site.register(models.MessageStatus)
