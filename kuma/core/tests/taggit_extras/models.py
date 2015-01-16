from django.db import models

from ...managers import NamespacedTaggableManager


class Food(models.Model):
    name = models.CharField(max_length=50)
    tags = NamespacedTaggableManager()

    def __unicode__(self):
        return self.name
