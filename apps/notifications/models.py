from django.db import models

from sumo.models import ModelBase


class EventWatch(ModelBase):
    content_type = models.CharField(max_length=100, db_index=True)
    watch_id = models.IntegerField(db_index=True)
    email = models.EmailField(db_index=True)

    class Meta:
        unique_together = (('content_type', 'watch_id', 'email'),)
