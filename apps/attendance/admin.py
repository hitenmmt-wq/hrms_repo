from django.contrib import admin

from apps.attendance import models
from apps.superadmin.admin import BaseAdmin

# Register your models here.

admin.site.register(models.EmployeeAttendance, BaseAdmin)
admin.site.register(models.AttendanceBreakLogs, BaseAdmin)
