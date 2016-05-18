# Fix the settings so that Whitenoise is happy
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuma.settings.local')

# Enable WhiteNoise
from django.core.wsgi import get_wsgi_application  # noqa
from whitenoise.django import DjangoWhiteNoise  # noqa

application = get_wsgi_application()
application = DjangoWhiteNoise(application)
