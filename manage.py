#!/usr/bin/env python
import os
import sys

import kuma

# setup sys.path to use vendor etc.
kuma.setup()

from django.core.management import execute_from_command_line

# Don't try to force a new setting module on us
if 'DJANGO_SETTINGS_MODULE' not in os.environ:

    # use settings_test.py for running tests
    if 'test' in sys.argv:
        settings_mod = 'kuma.settings.test'
    else:
        settings_mod = 'kuma.settings.local'

    # override the env var with what we want
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_mod

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
