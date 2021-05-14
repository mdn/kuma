#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kuma.settings.local")

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
