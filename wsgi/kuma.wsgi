import os
import site
from datetime import datetime

# Remember when mod_wsgi loaded this file so we can track it in nagios.
wsgi_loaded = datetime.now()

# For New Relic.
try:
    import newrelic.agent
except ImportError:
    newrelic = False

if newrelic:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)
    else:
        newrelic = False

# This is what mod_wsgi runs.
from django.core.wsgi import get_wsgi_application
django_app = get_wsgi_application()

# Enable WhiteNoise
from whitenoise.django import DjangoWhiteNoise
django_app = DjangoWhiteNoise(django_app)

# Normally we could let WSGIHandler run directly, but while we're dark
# launching, we want to force the script name to be empty so we don't create
# any /z links through reverse.  This fixes bug 554576.
def application(env, start_response):
    from django.conf import settings
    if 'HTTP_X_ZEUS_DL_PT' in env:
        env['SCRIPT_URL'] = env['SCRIPT_NAME'] = ''
    env['wsgi.loaded'] = wsgi_loaded
    env['platform.name'] = settings.PLATFORM_NAME
    return django_app(env, start_response)
