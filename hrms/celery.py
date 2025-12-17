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
        "schedule": crontab(minute=10, hour=10, day_of_month=17, month_of_year=12),
    }
}
