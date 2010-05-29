from django.db import models
from django.contrib.contenttypes.models import ContentType

from sumo.models import ModelBase


class EventWatch(ModelBase):
    """
    Allows anyone to watch a specific item for changes. Uses email instead of
    user ID so anonymous visitors can also watch things eventually.
    """

    content_type = models.ForeignKey(ContentType)
    watch_id = models.IntegerField(db_index=True)
    email = models.EmailField(db_index=True)

    class Meta:
        unique_together = (('content_type', 'watch_id', 'email'),)
