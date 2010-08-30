from datetime import datetime

from django.db import models

from sumo.models import ModelBase


class Tweet(ModelBase):
    """An entry on twitter."""
    tweet_id = models.BigIntegerField()
    raw_json = models.TextField()
    locale = models.CharField(max_length=20, db_index=True)
    created = models.DateTimeField(default=datetime.now, db_index=True)

    class Meta:
        get_latest_by = 'created'
        ordering = ('-created',)
