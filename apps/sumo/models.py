from django.conf import settings
from django.db import models

import caching.base

# Our apps should subclass ManagerBase instead of models.Manager or
# caching.base.CachingManager directly.
ManagerBase = caching.base.CachingManager


class ModelBase(caching.base.CachingMixin, models.Model):
    """
    Base class for SUMO models to abstract some common features.

    * Caching.
    """

    objects = ManagerBase()
    uncached = models.Manager()

    class Meta:
        abstract = True


class LocaleField(models.CharField):
    """CharField with locale settings specific to SUMO defaults."""
    def __init__(self, max_length=7, db_index=True,
                 default=settings.LANGUAGE_CODE,
                 choices=settings.LANGUAGE_CHOICES, *args, **kwargs):
        return super(LocaleField, self).__init__(
            max_length=max_length, db_index=db_index,
            default=default, choices=choices, *args, **kwargs)
