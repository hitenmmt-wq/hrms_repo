from django.db import models
from apps.base.models import BaseModel
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Users(AbstractUser):
    username = None
    role = models.CharField(max_length=50, null=True, blank=True, default="employee")
    email = models.EmailField(unique=True, null=True, blank=True)
    # department = models.ForeignKey("Department", on_delete=models.CASCADE, related_name="user_department", null=True, blank=True)
    # salary = models.FloatField(default=0.0)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.email
    
class Department(BaseModel):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Holiday(BaseModel):
    name = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return self.name
    
    
class Leave(BaseModel):
    LEAVE_TYPE = (
        ("casual", "casual"),
        ("sick", "sick"),
        ("maternity", "maternity"),
        ("privilege ", "privilege "),
        ("other", "other"),
    )
    user = models.ForeignKey("Users", on_delete=models.CASCADE, related_name="user_leaves")
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE, default="other")
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=50, default="pending")

    def __str__(self):
        return f"{self.user.email} - {self.leave_type} - {self.status}"
    

class Attendance(BaseModel):
    ATTENDANCE_TYPE = (
        ("present", "present"),
        ("unpaid_leave", "unpaid_leave"),
        ("paid_leave", "paid_leave"),
        ("half_day", "half_day"),
        ("incomplete_hours", "incomplete_hours"),
        ("pending", "pending"),
    )
    user = models.ForeignKey("Users", on_delete=models.CASCADE, related_name="user_attendance")
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    total_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default="pending", choices=ATTENDANCE_TYPE)

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.status}"