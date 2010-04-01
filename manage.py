#!/usr/bin/env python
import os
import site

from django.core.management import execute_manager, setup_environ


ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

site.addsitedir(path('apps'))
site.addsitedir(path('lib'))

try:
    import settings_local as settings
except ImportError:
    try:
        import settings # Assumed to be in the same directory.
    except ImportError:
        import sys
        sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
        sys.exit(1)


# The first thing execute_manager does is call `setup_environ`.  Logging config
# needs to access settings, so we'll setup the environ early.
setup_environ(settings)

# Import for side-effect: configures our logging handlers.
import log_settings


if __name__ == "__main__":
    execute_manager(settings)
