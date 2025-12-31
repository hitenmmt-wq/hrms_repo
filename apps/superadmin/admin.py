from django.contrib import admin

from apps.superadmin import models

# Register your models here.

admin.site.register(models.Users)
admin.site.register(models.Holiday)
admin.site.register(models.Department)
admin.site.register(models.Position)
admin.site.register(models.Announcement)
admin.site.register(models.Leave)
admin.site.register(models.LeaveType)
admin.site.register(models.SettingData)
admin.site.register(models.CommonData)
