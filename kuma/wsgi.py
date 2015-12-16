import os
import site

# Add the Kuma root dir to the python path so we can import manage.
this_dir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(this_dir, '..')))

# manage adds /lib, and /vendor to the Python path.
import manage  # noqa

# Enable WhiteNoise
from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise
application = get_wsgi_application()
application = DjangoWhiteNoise(application)
