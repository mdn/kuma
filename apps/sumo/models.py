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
