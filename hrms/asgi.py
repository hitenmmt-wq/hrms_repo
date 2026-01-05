"""
ASGI config for hrms project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")

django.setup()

from . import routing  # noqa

django_asgi_app = get_asgi_application()

application = routing.application
