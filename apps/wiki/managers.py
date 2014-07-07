from django.db import models

from .queries import TransformQuerySet


class TransformManager(models.Manager):

    def get_query_set(self):
        return TransformQuerySet(self.model)
