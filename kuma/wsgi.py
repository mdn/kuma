# Fix the settings so that Whitenoise is happy
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_local')

# Enable WhiteNoise
from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise
application = get_wsgi_application()
application = DjangoWhiteNoise(application)
