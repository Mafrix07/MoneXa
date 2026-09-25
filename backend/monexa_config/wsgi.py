"""WSGI config for MoneXa."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monexa_config.settings")
application = get_wsgi_application()
