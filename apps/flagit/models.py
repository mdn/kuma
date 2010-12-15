from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from tower import ugettext_lazy as _lazy

from sumo.models import ModelBase, ManagerBase


class FlaggedObjectManager(ManagerBase):
    def pending(self):
        """Get all flagged objects that are pending moderation."""
        return self.filter(status=0)


class FlaggedObject(ModelBase):
    """A flag raised on an object."""

    REASONS = (
        ('spam', _lazy(u'Spam or other unrelated content')),
        ('language', _lazy(u'Inappropriate language/dialog')),
        ('bug_support', _lazy(u'Misplaced bug report or support request')),
        ('other', _lazy(u'Other (please specify)')),
    )

    STATUSES = (
        (0, _lazy(u'Pending')),
        (1, _lazy(u'Accepted and Fixed')),
        (2, _lazy(u'Rejected')),
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    status = models.IntegerField(default=0, db_index=True, choices=STATUSES)
    reason = models.CharField(max_length=64, choices=REASONS)
    notes = models.TextField(default='', blank=True)

    creator = models.ForeignKey(User, related_name='flags')
    created = models.DateTimeField(default=datetime.now, db_index=True)

    handled = models.DateTimeField(default=datetime.now, db_index=True)
    handled_by = models.ForeignKey(User, null=True)

    objects = FlaggedObjectManager()

    class Meta:
        unique_together = (('content_type', 'object_id', 'creator'),)
        ordering = ['created']
        permissions = (
                ('can_moderate',
                 'Can moderate flagged objects'),
            )
