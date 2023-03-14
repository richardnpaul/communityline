"""
ASGI config for villageline project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

# Standard Library Imports
import os

# Django Imports
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villageline.settings.local')

application = get_asgi_application()
