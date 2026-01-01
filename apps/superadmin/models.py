from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.base import constants
from apps.base.models import BaseModel

# Create your models here.


class CommonData(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    company_link = models.CharField(max_length=255, null=True, blank=True)
    company_logo = models.ImageField(upload_to="company_logo", null=True, blank=True)
    pl_leave = models.IntegerField(default=12, null=True, blank=True)
    sl_leave = models.IntegerField(default=4, null=True, blank=True)
    lop_leave = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name


class SettingData(BaseModel):
    email_host = models.CharField(max_length=255, null=True, blank=True)
    email_port = models.IntegerField(null=True, blank=True)
    email_host_user = models.CharField(max_length=255, null=True, blank=True)
    email_host_password = models.CharField(max_length=255, null=True, blank=True)
    email_use_tls = models.BooleanField(default=True)
    email_use_ssl = models.BooleanField(default=False)

    database_name = models.CharField(max_length=255, null=True, blank=True)
    database_user = models.CharField(max_length=255, null=True, blank=True)
    database_password = models.CharField(max_length=255, null=True, blank=True)
    database_host = models.CharField(max_length=255, null=True, blank=True)
    database_port = models.CharField(max_length=255, null=True, blank=True)

    time_zone = models.CharField(max_length=255, null=True, blank=True)

    access_token_lifetime = models.IntegerField(default=1)
    refresh_token_lifetime = models.IntegerField(default=7)

    celery_broker_url = models.CharField(max_length=255, null=True, blank=True)
    celery_result_backend = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.time_zone


class Users(AbstractUser):
    username = None
    role = models.CharField(max_length=50, null=True, blank=True, default="employee")
    email = models.EmailField(unique=True)
    department = models.ForeignKey(
        "Department",
        on_delete=models.CASCADE,
        related_name="user_department",
        null=True,
        blank=True,
    )
    profile = models.ImageField(upload_to="profile", null=True, blank=True)
    employee_id = models.CharField(max_length=50, null=True, blank=True)
    position = models.ForeignKey(
        "Position",
        on_delete=models.CASCADE,
        related_name="user_position",
        null=True,
        blank=True,
    )
    joining_date = models.DateTimeField(null=True, blank=True)
    birthdate = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["employee_id"]),
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["department"]),
            models.Index(fields=["birthdate"]),
        ]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} - {self.employee_id} - {self.role}"


class Department(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Announcement(BaseModel):
    title = models.CharField(max_length=225)
    description = models.TextField()
    date = models.DateTimeField()

    def __str__(self):
        return self.title


class Position(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Holiday(BaseModel):
    name = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.date}"


class LeaveType(BaseModel):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"


class Leave(BaseModel):
    HALF_DAY_PART = (
        ("first", "First"),
        ("second", "Second"),
    )
    employee = models.ForeignKey(
        "Users", on_delete=models.CASCADE, related_name="user_leaves"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="leave_type",
        null=True,
        blank=True,
    )
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    day_part = models.CharField(
        max_length=50, choices=HALF_DAY_PART, null=True, blank=True
    )
    total_days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reason = models.TextField()
    status = models.CharField(max_length=50, default="pending")

    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        Users,
        null=True,
        blank=True,
        related_name="approved_leaves",
        on_delete=models.SET_NULL,
    )
    response_text = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["employee", "from_date", "to_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.leave_type} - {self.status}"

    def save(self, *args, **kwargs):
        if self.leave_type.code == constants.HALFDAY_LEAVE:
            self.total_days = 0.5
        elif not self.to_date:
            self.total_days = 1
        else:
            self.total_days = (self.to_date - self.from_date).days + 1
        super().save(*args, **kwargs)
