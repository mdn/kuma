from django.db import models

from sumo.models import ModelBase


class Redirect(ModelBase):
    product = models.CharField(max_length=30, blank=True, db_index=True)
    version = models.CharField(max_length=30, blank=True, db_index=True)
    platform = models.CharField(max_length=30, blank=True, db_index=True)
    locale = models.CharField(max_length=10, blank=True, db_index=True)
    topic = models.CharField(max_length=50, blank=True, db_index=True)
    target = models.CharField(max_length=100)

    class Meta:
        unique_together = ('product', 'version', 'platform',
                           'locale', 'topic')

    def __unicode__(self):
        parts = (
            self.product or '*',
            self.version or '*',
            self.platform or '*',
            self.locale or '*',
            self.topic or '',
            self.target
        )
        return u'%s/%s/%s/%s/%s -> %s' % parts
