from django.conf import settings
from django.db import models

from south.modelsinspector import add_introspection_rules


class LocaleField(models.CharField):
    """CharField with locale settings specific to SUMO defaults."""
    def __init__(self, max_length=7, default=settings.LANGUAGE_CODE,
                 choices=settings.LANGUAGES, *args, **kwargs):
        return super(LocaleField, self).__init__(
            max_length=max_length, default=default, choices=choices,
            *args, **kwargs)

add_introspection_rules([], ["^sumo\.models\.LocaleField"])
