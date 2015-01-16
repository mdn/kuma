import logging

from django.conf import settings


# fill this in for django 1.4
class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return settings.DEBUG
