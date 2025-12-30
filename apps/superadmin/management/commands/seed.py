from django.apps import apps
from django.contrib import admin

# from django.contrib.admin.sites import AlreadyRegistered
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.superadmin.models import Users


class Command(BaseCommand):
    help = "Runs makemigrations, migrate and auto-registers models in admin."

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.SUCCESS("Running makemigrations..."))
        call_command("makemigrations")

        self.stdout.write(self.style.SUCCESS("Running migrate..."))
        call_command("migrate")

        self.create_default_superuser()

        self.stdout.write(self.style.SUCCESS("Auto-registering models in admin..."))
        self.register_models()

        self.stdout.write(self.style.SUCCESS("Done"))

    def create_default_superuser(self):
        """
        Create default admin superuser if not exists.
        """
        password = "admin"
        email = "admin@example.com"

        if not Users.objects.filter(email=email).exists():
            user = Users.objects.create(
                email=email,
                is_superuser=True,
                is_staff=True,
                is_active=True,
                role="admin",
            )
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser created → email: {email}, password: {password}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Superuser 'admin' already exists. Skipping creation."
                )
            )

    def register_models(self):
        """
        Auto-register all models to Django admin.
        """
        for model in apps.get_models():
            if model not in admin.site._registry:
                try:
                    admin.site.register(model)
                    self.stdout.write(
                        self.style.SUCCESS(f"Registered: {model.__name__}")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {model.__name__}: {str(e)}")
                    )
