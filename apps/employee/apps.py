from django.apps import AppConfig


class EmployeeConfig(AppConfig):
    name = "apps.employee"

    def ready(self):
        import apps.employee.signals  # noqa: F401
