"""Models for activity counters"""

import logging

from django.db import models
from django.conf import settings
from django.db.models import F

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

from django.utils.translation import ugettext_lazy as _

from .utils import get_ip, get_unique
from .fields import ActionCounterField


class TestModel(models.Model):
    # TODO: Find a way to move this to tests.py and create only during testing!

    title = models.CharField(max_length=255, blank=False, unique=True)

    likes = ActionCounterField()
    views = ActionCounterField(max_total_per_unique=5)
    frobs = ActionCounterField(min_total_per_unique=-5)
    boogs = ActionCounterField(min_total_per_unique=-5, max_total_per_unique=5)
    
    def __unicode__(self):
        return unicode(self.pk)


class ActionCounterUniqueManager(models.Manager):
    """Manager for action hits"""

    def get_unique_for_request(self, object, action_name, request, create=True):
        """Get a unique counter for the given request, with the option to
        refrain from creating a new one if the intent is just to check
        existence."""
        content_type = ContentType.objects.get_for_model(object)
        user, ip, user_agent, session_key = get_unique(request)
        if create:
            return self.get_or_create(
                    content_type=content_type, object_pk=object.pk, 
                    name=action_name,
                    ip=ip, user_agent=user_agent, user=user,
                    session_key=session_key,
                    defaults=dict( total=0 ))
        else:
            try:
                return ( 
                    self.get(
                        content_type=content_type, object_pk=object.pk, 
                        name=action_name,
                        ip=ip, user_agent=user_agent, user=user,
                        session_key=session_key,), 
                    False 
                )
            except ActionCounterUnique.DoesNotExist:
                return ( None, False )


class ActionCounterUnique(models.Model):
    """Action counter for a unique request / user"""
    objects = ActionCounterUniqueManager()

    content_type = models.ForeignKey(
            ContentType,
            verbose_name="content type",
            related_name="content_type_set_for_%(class)s",)
    object_pk = models.CharField( _('object ID'),
            max_length=32)
    content_object = generic.GenericForeignKey(
            'content_type', 'object_pk')
    name = models.CharField( _('name of the action'),
            max_length=64, db_index=True, blank=False)

    total = models.IntegerField()

    ip = models.CharField(max_length=40, editable=False, 
            db_index=True, blank=True, null=True)
    session_key = models.CharField(max_length=40, editable=False, 
            db_index=True, blank=True, null=True)
    user_agent = models.CharField(max_length=128, editable=False, 
            db_index=True, blank=True, null=True)
    user = models.ForeignKey(User, editable=False, 
            db_index=True, blank=True, null=True)

    modified = models.DateTimeField( 
            _('date last modified'), 
            auto_now=True, blank=False)

    def increment(self, min=0, max=1):
        return self._change_total(1, min, max)

    def decrement(self, min=0, max=1):
        return self._change_total(-1, min, max)

    def _change_total(self, delta, min, max):
        # TODO: This seems like a race condition. Maybe there's a way to do something like
        # UPDATE actioncounterunique SET total = min(max(field_total+1, min), max) WHERE ...
        # ...and if that's doable, how to detect whether the total changed
        result = (self.total + delta)
        if result > max: return False
        if result < min: return False
        if result == 0:
            # Don't keep zero entries around in the table.
            self.delete()
        else:
            self.total = F('total') + delta
            self.save()
        return True

