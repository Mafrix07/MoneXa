"""ASGI config for MoneXa."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monexa_config.settings")
application = get_asgi_application()
