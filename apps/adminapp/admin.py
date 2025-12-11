from django.contrib import admin
from apps.adminapp import models
# Register your models here.

admin.site.register(models.Users)
admin.site.register(models.Holiday)
admin.site.register(models.Department)