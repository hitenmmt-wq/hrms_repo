from django.contrib import admin

from apps.attendance import models

# Register your models here.

admin.site.register(models.EmployeeAttendance)
admin.site.register(models.AttendanceBreakLogs)
