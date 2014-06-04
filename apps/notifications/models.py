import hashlib

from django.db import models, connections, router
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from devmo.models import ModelBase
from sumo.models import LocaleField
from sumo.urlresolvers import reverse


def multi_raw(query, params, models):
    """Scoop multiple model instances out of the DB at once, given a query that
    returns all fields of each.

    Return an iterable of sequences of model instances parallel to the `models`
    sequence of classes. For example...

        [(<User such-and-such>, <Watch such-and-such>), ...]

    """
    cursor = connections[router.db_for_read(models[0])].cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    model_attnames = dict((m, [f.get_attname() for f in m._meta._fields()])
                          for m in models)
    for row in rows:
        next_value = iter(row).next
        yield [model_class(**dict((a, next_value())
                           for a in model_attnames[model_class]))
               for model_class in models]


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
    locale = LocaleField(default='', db_index=True)
    email = models.EmailField(db_index=True)
    hash = models.CharField(max_length=40, null=True, db_index=True)

    class Meta:
        unique_together = (('content_type', 'watch_id', 'email',
                            'event_type', 'locale'),)

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
        from sumo.helpers import urlparams
        url_ = reverse('notifications.remove', args=[self.key])
        return urlparams(url_, email=self.email)


class Watch(ModelBase):
    """Watch events."""
    # Key used by an Event to find watches it manages:
    event_type = models.CharField(max_length=30, db_index=True)

    # Optional reference to a content type:
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(db_index=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(User, null=True, blank=True)

    # Email stored only in the case of anonymous users:
    email = models.EmailField(db_index=True, null=True, blank=True)

    # Secret for activating anonymous watch email addresses.
    secret = models.CharField(max_length=10, null=True, blank=True)
    # Active watches receive notifications, inactive watches don't.
    is_active = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        rest = self.content_object or self.content_type or self.object_id
        return u'[%s] %s, %s' % (self.pk, self.event_type, str(rest))

    def activate(self):
        """Enable this watch so it actually fires.

        Return self to support method chaining.

        """
        self.is_active = True
        return self


class WatchFilter(ModelBase):
    """Additional key/value pairs that pare down the scope of a watch"""
    watch = models.ForeignKey(Watch, related_name='filters')
    name = models.CharField(max_length=20)

    # Either an int or the hash of an item in a reasonably small set, which is
    # indicated by the name field. See comments by hash_to_unsigned() for more
    # on what is reasonably small.
    value = models.PositiveIntegerField()

    class Meta(object):
        # There's no particular reason we couldn't allow multiple values for
        # one name to be ORed together, but the API needs a little work
        # (accepting lists passed to notify()) to support that.
        #
        # This ordering makes the index usable for lookups by name.
        unique_together = ('name', 'watch')


class NotificationsMixin(models.Model):
    """Mixin for notifications models that adds watches as a generic relation.

    So we get cascading deletes for free, yay!

    """
    watches = generic.GenericRelation(Watch,
                  related_name='%(app_label)s_%(class)s_watches')

    class Meta(object):
        abstract = True


class EmailUser(AnonymousUser):
    """An anonymous user identified only by email address"""

    def __init__(self, email=''):
        self.email = email

    def __unicode__(self):
        return 'Anonymous user <%s>' % self.email

    __repr__ = AnonymousUser.__str__

    def __eq__(self, other):
        return self.email == other.email

    def __ne__(self, other):
        return self.email != other.email

    def __hash__(self):
        return hash(self.email)

    def is_anonymous(self):
        return False
