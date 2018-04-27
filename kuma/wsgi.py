# Fix the settings so that Whitenoise is happy
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuma.settings.local')

# Enable WhiteNoise
from django.core.wsgi import get_wsgi_application  # noqa

# TODO: Remove with Django 1.11
# Monkey-patch the Django CSRF functionality prior to loading everything else.
import kuma.core  # noqa

application = get_wsgi_application()
