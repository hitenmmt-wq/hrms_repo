import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")

app = Celery("hrms")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.enable_utc = False
app.conf.timezone = settings.TIME_ZONE  # "Asia/Kolkata"

app.conf.beat_schedule = {
    "credit-leave-balances-yearly": {
        "task": "apps.employee.tasks.credit_new_year_employee_leaves",
        "schedule": crontab(minute=5, hour=0, day_of_month=1, month_of_year=1),
    },
    "add-absent-employees-attendance": {
        "task": "apps.employee.tasks.update_employee_absent_leaves",
        "schedule": crontab(minute=59, hour=23),
    },
    "employee-birthday-update": {
        "task": "apps.employee.tasks.notify_employee_birthday",
        "schedule": crontab(minute=5, hour=9),
    },
    "late-comers-notification": {
        "task": "apps.employee.tasks.notify_frequent_late_comings",
        "schedule": crontab(minute=0, hour=13),
    },
    "generate-monthly-payslips": {
        "task": "apps.employee.tasks.generate_monthly_payslips",
        "schedule": crontab(minute=0, hour=9, day_of_month=5),
    },
    "auto_checkout_employees": {
        "task": "apps.employee.tasks.auto_checkout_employees",
        "schedule": crontab(minute=59, hour=23),  # Every day at 11:59 PM
    },
}
