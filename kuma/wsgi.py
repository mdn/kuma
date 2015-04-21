import os

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

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
