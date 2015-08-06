from django.conf import settings
from django.db import models


class LocaleField(models.CharField):
    """CharField with locale settings specific to Kuma defaults."""
    def __init__(self, max_length=7, default=settings.LANGUAGE_CODE,
                 choices=settings.LANGUAGES, *args, **kwargs):
        return super(LocaleField, self).__init__(
            max_length=max_length, default=default, choices=choices,
            *args, **kwargs)
