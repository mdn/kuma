#!/usr/bin/env python
import os
import sys

# Now we can import from third-party libraries.
from django.core.management import execute_from_command_line

# Don't try to force a new setting module on us
if 'DJANGO_SETTINGS_MODULE' not in os.environ:

    # use settings_test.py for running tests
    if 'test' in sys.argv:
        settings_mod = 'settings_test'
    else:
        # or try the optional "local" settings module first
        try:
            import settings_local  # noqa
        except ImportError:
            # or use the plain settings.py module
            settings_mod = 'settings'
        else:
            settings_mod = 'settings_local'

    # override the env var with what we want
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_mod

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
