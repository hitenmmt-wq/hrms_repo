"""
ASGI config for hrms project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")

django.setup()

from apps.notification import routing  # noqa

application = routing.application
