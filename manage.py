#!/usr/bin/env python
import os
import site
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def path(*parts):
    return os.path.join(ROOT, *parts)

prev_sys_path = list(sys.path)

site.addsitedir(path('vendor'))

# Move the new items to the front of sys.path.
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

# Now we can import from third-party libraries.
from django.core.management import execute_from_command_line

settings_mod = 'settings'

try:
    import settings_local
    settings_mod = 'settings_local'
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_mod)

import jingo.monkey
jingo.monkey.patch()

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
