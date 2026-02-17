from django.contrib import admin

from apps.notification import models

# Register your models here.

admin.site.register(models.NotificationType)
admin.site.register(models.Notification)
