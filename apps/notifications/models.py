import hashlib

from django.db import models
from django.contrib.contenttypes.models import ContentType

from sumo.models import ModelBase
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams


class EventWatch(ModelBase):
    """
    Allows anyone to watch a specific item for changes. Uses email instead of
    user ID so anonymous visitors can also watch things eventually.
    """

    content_type = models.ForeignKey(ContentType)
    # If watch_id is set to null, then the watch is for the model and not
    # an instance.
    watch_id = models.IntegerField(db_index=True, null=True)
    event_type = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(db_index=True)
    hash = models.CharField(max_length=40, null=True, db_index=True)

    class Meta:
        unique_together = (('content_type', 'watch_id', 'email',
                            'event_type'),)

    @property
    def key(self):
        if self.hash:
            return self.hash

        key_ = '%s-%s-%s-%s' % (self.content_type.id, self.watch_id,
                                self.email, self.event_type)
        sha = hashlib.sha1()
        sha.update(key_)
        return sha.hexdigest()

    def save(self, *args, **kwargs):
        """Overriding save to set the hash."""
        self.hash = self.key

        super(EventWatch, self).save(*args, **kwargs)

    def get_remove_url(self):
        """Get the URL to remove an EventWatch."""
        url_ = reverse('notifications.remove', args=[self.key])
        return urlparams(url_, email=self.email)
