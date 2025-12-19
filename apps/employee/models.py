from django.db import models
from django.utils import timezone

from apps.base.models import BaseModel
from apps.superadmin.models import Users

# Create your models here.


def current_year():
    return timezone.now().year


class LeaveBalance(BaseModel):
    employee = models.OneToOneField(
        Users, on_delete=models.CASCADE, related_name="employee_leave_balance"
    )
    pl = models.IntegerField(default=12, null=True, blank=True)
    sl = models.IntegerField(default=4, null=True, blank=True)
    lop = models.IntegerField(default=0, null=True, blank=True)
    used_pl = models.IntegerField(default=0, null=True, blank=True)
    used_sl = models.IntegerField(default=0, null=True, blank=True)
    used_lop = models.IntegerField(default=0, null=True, blank=True)
    year = models.IntegerField(default=current_year, null=True, blank=True)

    class Meta:
        unique_together = ("employee", "year")

    def __str__(self):
        return f"{self.employee.email} - {self.year}"


class PaySlip(BaseModel):
    employee = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="employee_payslips"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    month = models.CharField(max_length=20, null=True, blank=True)
    days = models.IntegerField(null=True, blank=True)
    basic_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    hr_allowance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    special_allowance = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_earnings = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    tax_deductions = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    other_deductions = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    leave_deductions = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    total_deductions = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    net_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.employee.email} - {self.month} Payslip"
