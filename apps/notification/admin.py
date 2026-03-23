from django.contrib import admin

from apps.notification import models
from apps.superadmin.admin import BaseAdmin

# Register your models here.

admin.site.register(models.NotificationType, BaseAdmin)
admin.site.register(models.Notification, BaseAdmin)
