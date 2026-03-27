from django.contrib import admin

from apps.superadmin import models

# Register your models here.


class BaseAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        # Get all field names dynamically
        fields = [field.name for field in self.model._meta.fields]

        # Ensure created_at and updated_at are included
        if "created_at" in fields and "updated_at" in fields:
            return fields
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly = []
        if hasattr(self.model, "created_at"):
            readonly.append("created_at")
        if hasattr(self.model, "updated_at"):
            readonly.append("updated_at")
        return readonly


admin.site.register(models.Users, BaseAdmin)
admin.site.register(models.Holiday, BaseAdmin)
admin.site.register(models.Department, BaseAdmin)
admin.site.register(models.Position, BaseAdmin)
admin.site.register(models.Announcement, BaseAdmin)
admin.site.register(models.Leave, BaseAdmin)
admin.site.register(models.LeaveType, BaseAdmin)
admin.site.register(models.SettingData, BaseAdmin)
admin.site.register(models.CommonData, BaseAdmin)
# admin.site.register(models.UserDeviceToken, BaseAdmin)
admin.site.register(models.DeviceActivity, BaseAdmin)
admin.site.register(models.DeviceConfigPolicy, BaseAdmin)

admin.site.register(models.Project, BaseAdmin)
admin.site.register(models.DailyReport, BaseAdmin)
admin.site.register(models.Client, BaseAdmin)


@admin.register(models.UserDeviceToken)
class UserDeviceTokenAdmin(BaseAdmin):
    list_display = (
        "user",
        "is_active",
        "device_name",
        "tracking_token",
        "fcm_token",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("user__email", "device_name")
