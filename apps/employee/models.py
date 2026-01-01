from django.db import models
from django.db.models import Q
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
    pl = models.FloatField(default=12, null=True, blank=True)
    sl = models.FloatField(default=4, null=True, blank=True)
    lop = models.FloatField(default=0, null=True, blank=True)
    used_pl = models.FloatField(default=0, null=True, blank=True)
    used_sl = models.FloatField(default=0, null=True, blank=True)
    used_lop = models.FloatField(default=0, null=True, blank=True)
    year = models.IntegerField(default=current_year, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["employee", "year"]),
            models.Index(fields=["year"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "year"],
                condition=Q(is_deleted=False),
                name="unique_active_employee_per_year",
            )
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.year}"

    @property
    def remaining_pl(self):
        return max(self.pl - self.used_pl, 0)

    @property
    def remaining_sl(self):
        return max(self.sl - self.used_sl, 0)

    @property
    def remaining_lop(self):
        return max(self.lop - self.used_lop, 0)


class PaySlip(BaseModel):
    employee = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="employee_payslips"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    month = models.CharField(max_length=20, null=True, blank=True)
    days = models.FloatField(null=True, blank=True)
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
    pdf_file = models.FileField(upload_to="payslips/", null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["employee", "month"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.month} Payslip"
