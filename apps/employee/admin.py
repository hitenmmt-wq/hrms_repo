from django.contrib import admin

from apps.employee import models
from apps.superadmin.admin import BaseAdmin

# Register your models here.


admin.site.register(models.LeaveBalance, BaseAdmin)
admin.site.register(models.PaySlip, BaseAdmin)
admin.site.register(models.TicketIssue, BaseAdmin)
