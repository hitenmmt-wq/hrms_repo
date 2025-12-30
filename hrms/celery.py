import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")

app = Celery("hrms")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


CELERY_BEAT_SCHEDULE = {
    "credit-leave-balances-yearly": {
        "task": "apps.employee.tasks.credit_new_year_employee_leaves",
        "schedule": crontab(minute=41, hour=15),
    },
    "add-absent-employees-attendance": {
        "task": "apps.employee.tasks.update_employee_absent_leaves",
        "schedule": crontab(minute=41, hour=15),
    },
    "employee-birthday-update": {
        "task": "apps.employee.tasks.notify_employee_birthday",
        "schedule": crontab(minute=41, hour=18),
    },
}
