from django.db import models

from ..fields import ActionCounterField


class TestModel(models.Model):
    title = models.CharField(max_length=255, blank=False, unique=True)

    likes = ActionCounterField()
    views = ActionCounterField(max_total_per_unique=5)
    frobs = ActionCounterField(min_total_per_unique=-5)
    boogs = ActionCounterField(min_total_per_unique=-5, max_total_per_unique=5)

    def __unicode__(self):
        return unicode(self.pk)
