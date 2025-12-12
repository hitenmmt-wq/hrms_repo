from django.db import models
from apps.base.models import BaseModel
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Users(AbstractUser):
    username = None
    role = models.CharField(max_length=50, null=True, blank=True, default="employee")
    email = models.EmailField(unique=True, null=True, blank=True)
    department = models.ForeignKey("Department", on_delete=models.CASCADE, related_name="user_department", null=True, blank=True)
    profile = models.ImageField(upload_to="profile", null=True, blank=True)
    employee_id = models.CharField(max_length=50, null=True, blank=True)
    position = models.ForeignKey("Position", on_delete=models.CASCADE, related_name="user_position", null=True, blank=True)
    joining_date = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.email
    
class Department(BaseModel):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Position(BaseModel):
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
    employee = models.ForeignKey("Users", on_delete=models.CASCADE, related_name="user_leaves")
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE, default="other")
    from_date = models.DateField()
    to_date = models.DateField(null=True, blank=True)
    total_days = models.IntegerField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=50, default="pending")
    
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(Users, null=True, blank=True, related_name="approved_leaves",on_delete=models.SET_NULL)
    response_text = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["employee", "from_date", "to_date"]),
            models.Index(fields=["status"]),
        ]
        
    def __str__(self):
        return f"{self.user.email} - {self.leave_type} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.to_date:
            self.total_days = 1
        else:
            self.total_days = (self.to_date - self.from_date).days + 1  
        super().save(*args, **kwargs)
            

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
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default="pending", choices=ATTENDANCE_TYPE)

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.status}"
    
    
# class EmployeeSalary(BaseModel):
#     user = models.ForeignKey("Users", on_delete=models.CASCADE, related_name="user_salary")
#     status = models.CharField(max_length=50, default="pending")
    
#     start_pay_period = models.DateField(null=True, blank=True)
#     end_pay_period = models.DateField(null=True, blank=True)
    
#     month = models.CharField(max_length=50)
#     year = models.CharField(max_length=50)
    
#     starting_salary = models.FloatField(default=0.0)
#     previous_salary = models.FloatField(default=0.0)
#     current_salary = models.FloatField(default=0.0)

#     def __str__(self):
#         return f"{self.user.email} - {self.month} - {self.year}"
    
# class EmployeePayslip(BaseModel):
#     employee_salary = models.ForeignKey("EmployeeSalary", on_delete=models.CASCADE, related_name="employee_payslip")
#     basic_fee = models.FloatField(default=0.0)
#     basic_fee = models.FloatField(default=0.0)
#     basic_fee = models.FloatField(default=0.0)
#     status = models.CharField(max_length=50, default="pending")
    

#     def __str__(self):
#         return f"{self.user.email} - {self.month} - {self.year}"