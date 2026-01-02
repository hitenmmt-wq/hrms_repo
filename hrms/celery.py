import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")

app = Celery("hrms")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.enable_utc = False
app.conf.timezone = "Asia/Kolkata"

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
}
