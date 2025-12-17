from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered


class Command(BaseCommand):
    help = "Runs makemigrations, migrate and auto-registers models in admin."

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.SUCCESS("Running makemigrations..."))
        call_command("makemigrations")

        self.stdout.write(self.style.SUCCESS("Running migrate..."))
        call_command("migrate")

        self.stdout.write(self.style.SUCCESS("Auto-registering models in admin..."))

        for model in apps.get_models():
            try:
                admin.site.register(model)
                self.stdout.write(f"Registered: {model.__name__}")
            except AlreadyRegistered:
                pass

        self.stdout.write(self.style.SUCCESS("Done"))
