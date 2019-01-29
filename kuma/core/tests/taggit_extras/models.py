from __future__ import unicode_literals

from django.db import models

from ...managers import NamespacedTaggableManager


class Food(models.Model):
    name = models.CharField(max_length=50)
    tags = NamespacedTaggableManager()
