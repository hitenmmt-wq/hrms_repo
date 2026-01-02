from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.employee import models
from apps.notification.models import NotificationType
from apps.superadmin.models import (
    Announcement,
    CommonData,
    Department,
    Holiday,
    Position,
    Users,
)


class Command(BaseCommand):
    help = "Initialize default master data for first-time deployment"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing default data..."))

        self.create_departments()
        self.create_positions()
        self.create_notification_types()
        self.create_common_data()
        self.create_user()
        self.create_announcement()
        self.create_holiday()
        self.create_leave_balance()

        self.stdout.write(self.style.SUCCESS("Default data initialization completed."))

    def create_departments(self):
        departments = ["HR", "Engineering", "Operations", "Finance"]

        for name in departments:
            obj, created = Department.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Department created: {name}"))

    def create_positions(self):
        positions = [
            "Software Engineer",
            "HR Executive",
            "Manager",
            "Python Developer",
            "React Developer",
        ]

        for name in positions:
            obj, created = Position.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Position created: {name}"))

    def create_notification_types(self):
        notifications = [
            {"code": "announcement", "name": "Announcement"},
            {"code": "approved", "name": "Attendance Approved"},
            {"code": "pending", "name": "Attendance Pending"},
            {"code": "attendance_reminder", "name": "Attendance Reminder"},
            {"code": "birthday", "name": "Birthday Wish"},
            {"code": "chat_message", "name": "Chat Message"},
            {"code": "general", "name": "General"},
            {"code": "leave_apply", "name": "Leave Apply"},
            {"code": "leave_approved", "name": "Leave Approved"},
            {"code": "leave_rejected", "name": "Leave Rejected"},
        ]

        for item in notifications:
            obj, created = NotificationType.objects.get_or_create(
                code=item["code"],
                defaults={"name": item["name"]},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"NotificationType created: {item['code']}")
                )

    def create_common_data(self):
        if not CommonData.objects.exists():
            CommonData.objects.create(
                name="MultiMind Technology",
                pl_leave=12,
                sl_leave=4,
                lop_leave=0,
            )
            self.stdout.write(self.style.SUCCESS("CommonData created"))
        else:
            self.stdout.write("CommonData already exists")

    def create_user(self):
        data = [
            {
                "email": "admin1@gmail.com",
                "first_name": "admin1_first",
                "last_name": "admin1_last",
                "is_superuser": True,
                "role": "admin",
                "password": "admin1",
                "joining_date": timezone.datetime.now(),
            },
            {
                "email": "admin2@gmail.com",
                "first_name": "admin2_first",
                "last_name": "admin2_last",
                "is_superuser": True,
                "role": "admin",
                "password": "admin2",
                "joining_date": timezone.datetime.now(),
            },
            {
                "email": "admin3@gmail.com",
                "first_name": "admin3_first",
                "last_name": "admin3_last",
                "is_superuser": True,
                "role": "admin",
                "password": "admin3",
                "joining_date": timezone.datetime.now(),
            },
            {
                "email": "employee1@gmail.com",
                "first_name": "employee1_first",
                "last_name": "employee1_last",
                "is_superuser": False,
                "role": "employee",
                "password": "employee1",
                "joining_date": timezone.datetime.now(),
            },
            {
                "email": "employee2@gmail.com",
                "first_name": "employee2_first",
                "last_name": "employee2_last",
                "is_superuser": False,
                "role": "employee",
                "password": "employee2",
                "joining_date": timezone.datetime.now(),
            },
            {
                "email": "employee3@gmail.com",
                "first_name": "employee3_first",
                "last_name": "employee3_last",
                "is_superuser": False,
                "role": "employee",
                "password": "employee3",
                "joining_date": timezone.datetime.now(),
            },
        ]

        for item in data:
            obj, created = Users.objects.get_or_create(
                email=item["email"],
                defaults={
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                    "is_superuser": item["is_superuser"],
                    "role": item["role"],
                    "joining_date": item["joining_date"],
                },
            )
            if created:
                obj.set_password(item["password"])
                obj.save()
                self.stdout.write(self.style.SUCCESS("Admin-Employee Users created"))

    def create_announcement(self):
        data = [
            {
                "title": "Announcement1",
                "description": "Announcement1 description",
                "date": timezone.datetime.now(),
            },
            {
                "title": "Announcement2",
                "description": "Announcement2 description",
                "date": timezone.datetime.now(),
            },
            {
                "title": "Announcement3",
                "description": "Announcement3 description",
                "date": timezone.datetime.now(),
            },
        ]

        for item in data:
            obj, created = Announcement.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "date": item["date"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS("Announcement created"))

    def create_holiday(self):
        data = [
            {
                "name": "Holiday1",
                "date": timezone.datetime.now(),
            },
            {
                "name": "Holiday2",
                "date": timezone.datetime.now(),
            },
            {
                "name": "Holiday3",
                "date": timezone.datetime.now(),
            },
        ]

        for item in data:
            obj, created = Holiday.objects.get_or_create(
                name=item["name"],
                defaults={
                    "date": item["date"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS("Holiday created"))

    def create_leave_balance(self):
        employees = Users.objects.filter(is_active=True)
        common_data = CommonData.objects.first()
        for employee in employees:
            if common_data:
                leave_balance = models.LeaveBalance(
                    employee=employee,
                    pl_leave=common_data.pl_leave,
                    sl_leave=common_data.sl_leave,
                    lop_leave=common_data.lop_leave,
                )
                leave_balance.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"LeaveBalance created for employee: {employee.email}"
                    )
                )
            else:
                self.stdout.write(self.style.ERROR("CommonData not found"))
