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
# admin.site.register(models.UserDeviceToken)
admin.site.register(models.DeviceActivity)
admin.site.register(models.DeviceConfigPolicy)


@admin.register(models.UserDeviceToken)
class UserDeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "device_name", "tracking_token", "fcm_token", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "device_name")
