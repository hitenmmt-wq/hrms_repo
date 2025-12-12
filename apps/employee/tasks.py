from celery import shared_task
from django.utils import timezone
from apps.adminapp import models


@shared_task
def credit_new_year_employee_leaves():
    current_year = timezone.now().year
    print(f"==>> current_year: {current_year}")
    new_year = current_year + 1
    print(f"==>> new_year: {new_year}")
    
    employees = models.Users.objects.filter(is_active=True)
    for employee in employees:
        leaves = LeaveBalance.objects.get_or_create(year=new_year, pl=12, sl=4, lop=0,employee=employee)
        print(leaves)
        
    print("done------------==============")
        
    