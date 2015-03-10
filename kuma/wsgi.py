import os
from datetime import datetime

# Remember when mod_wsgi loaded this file so we can track it in nagios.
wsgi_loaded = datetime.now()

# For New Relic.
try:
    import newrelic.agent
except ImportError:
    pass
else:
    newrelic_ini = os.getenv('NEWRELIC_PYTHON_INI_FILE', False)
    if newrelic_ini:
        newrelic.agent.initialize(newrelic_ini)

# manage adds /lib, and /vendor to the Python path.
from . import setup
setup()

# This is what mod_wsgi runs.
from django.core.wsgi import get_wsgi_application
django_application = get_wsgi_application()


def application(env, start_response):
    """
    Normally we could let WSGIHandler run directly, but while we're dark
    launching, we want to force the script name to be empty so we don't create
    any /z links through reverse. This fixes bug 554576.
    """
    if 'HTTP_X_ZEUS_DL_PT' in env:
        env['SCRIPT_URL'] = env['SCRIPT_NAME'] = ''
    env['wsgi.loaded'] = wsgi_loaded
    return django_application(env, start_response)
