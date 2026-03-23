from django.contrib import admin

from apps.chat import models
from apps.superadmin.admin import BaseAdmin

# Register your models here.

admin.site.register(models.Conversation, BaseAdmin)
admin.site.register(models.Message, BaseAdmin)
admin.site.register(models.MessageStatus, BaseAdmin)
admin.site.register(models.MessageReaction, BaseAdmin)
