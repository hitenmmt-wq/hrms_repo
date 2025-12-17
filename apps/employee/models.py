from django.db import models
from apps.base.models import BaseModel
from apps.superadmin.models import Users
from django.utils import timezone

# Create your models here.


class LeaveBalance(models.Model):
    employee = models.OneToOneField(
        Users, on_delete=models.CASCADE, related_name="employee_leave_balance"
    )
    pl = models.IntegerField(default=12, null=True, blank=True)
    sl = models.IntegerField(default=4, null=True, blank=True)
    lop = models.IntegerField(default=0, null=True, blank=True)
    year = models.IntegerField(default=timezone.now().year, null=True, blank=True)

    class Meta:
        unique_together = ("employee", "year")

    def __str__(self):
        return f"{self.employee.email} - {self.year}"
