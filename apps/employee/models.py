"""
Employee models for leave balance and payroll management.

Handles employee-specific data including leave balances, payslip generation,
and salary calculations for the HRMS payroll system.
"""

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.base.models import BaseModel
from apps.base.validators import BaseValidator
from apps.superadmin.models import Users


def current_year():
    """Get current year for default leave balance year."""
    return timezone.now().year


class LeaveBalance(BaseModel):
    """Employee leave balance tracking with yearly allocation and usage."""

    employee = models.OneToOneField(
        Users, on_delete=models.CASCADE, related_name="employee_leave_balance"
    )
    pl = models.FloatField(default=0, null=True, blank=True)
    sl = models.FloatField(default=0, null=True, blank=True)
    lop = models.FloatField(default=0, null=True, blank=True)
    used_pl = models.FloatField(default=0, null=True, blank=True)
    used_sl = models.FloatField(default=0, null=True, blank=True)
    used_lop = models.FloatField(default=0, null=True, blank=True)
    year = models.IntegerField(
        default=current_year,
        null=True,
        blank=True,
        validators=[BaseValidator.validate_positive_number],
    )

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
        return f"{self.employee.email} - {self.year} - PL:{self.used_pl}, SL:{self.used_sl}, LOP:{self.used_lop}"

    @property
    def remaining_pl(self):
        """Calculate remaining privilege leave balance."""
        return max(self.pl - self.used_pl, 0)

    @property
    def remaining_sl(self):
        """Calculate remaining sick leave balance."""
        return max(self.sl - self.used_sl, 0)

    @property
    def remaining_lop(self):
        """Calculate remaining loss of pay balance."""
        return max(self.used_lop, 0)


class PaySlip(BaseModel):
    """Employee payslip with salary breakdown and deductions."""

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


class TicketIssue(BaseModel):
    employee = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="employee_tickets"
    )
    title = models.TextField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=100, default="open")
    priority = models.CharField(max_length=100, default="low")
    raised_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class Item(BaseModel):
    """Inventory item master — tracks available gadgets/assets."""

    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    purchased_at = models.DateTimeField()
    purchased_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchased_items",
    )

    class Meta:
        indexes = [models.Index(fields=["name"])]

    def __str__(self):
        return self.name


class InventoryDetail(BaseModel):
    """Tracks items allotted to employees."""

    employee = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="employee_inventory"
    )
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="item_inventory"
    )
    quantity = models.PositiveIntegerField(default=1)
    allotment_date = models.DateTimeField()
    alloted_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_alloted_by",
    )

    class Meta:
        indexes = [models.Index(fields=["employee", "item"])]

    def __str__(self):
        return f"{self.employee.email} - {self.item.name}"
