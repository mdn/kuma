"""Models for activity counters"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from kuma.core.utils import get_unique


class ActionCounterUniqueManager(models.Manager):
    """Manager for action hits"""

    def get_unique_for_request(self, object, action_name, request, create=True):
        """
        Get a unique counter for the given request, with the option to
        refrain from creating a new one if the intent is just to check
        existence.
        """
        content_type = ContentType.objects.get_for_model(object)
        user, ip, user_agent, unique_hash = get_unique(content_type, object.pk,
                                                       name=action_name,
                                                       request=request)
        if create:
            return self.get_or_create(
                unique_hash=unique_hash,
                defaults=dict(content_type=content_type, object_pk=object.pk,
                              name=action_name, ip=ip,
                              user_agent=user_agent, user=user,
                              total=0))
        else:
            try:
                return (self.get(unique_hash=unique_hash), False)
            except ActionCounterUnique.DoesNotExist:
                return (None, False)


class ActionCounterUnique(models.Model):
    """Action counter for a unique request / user"""

    objects = ActionCounterUniqueManager()

    content_type = models.ForeignKey(ContentType, verbose_name="content type",
                                     related_name="content_type_set_for_%(class)s",)
    object_pk = models.CharField(_('object ID'), max_length=32)
    content_object = GenericForeignKey('content_type', 'object_pk')
    name = models.CharField(_('name of the action'), max_length=64,
                            db_index=True, blank=False)

    total = models.IntegerField()

    ip = models.CharField(max_length=40, editable=False,
                          db_index=True, blank=True, null=True)
    user_agent = models.CharField(max_length=128, editable=False,
                                  db_index=True, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False,
                             db_index=True, blank=True, null=True)

    # HACK: As it turns out, MySQL doesn't consider two rows with NULL values
    # in a column as duplicates. So, resorting to calculating a unique hash in
    # code.
    unique_hash = models.CharField(max_length=32, editable=False,
                                   unique=True, db_index=True, null=True)

    modified = models.DateTimeField(_('date last modified'),
                                    auto_now=True, blank=False)

    def save(self, *args, **kwargs):
        # Ensure unique_hash is updated whenever the object is saved
        user, ip, user_agent, unique_hash = get_unique(
            self.content_type, self.object_pk, name=self.name,
            ip=self.ip, user_agent=self.user_agent, user=self.user)
        self.unique_hash = unique_hash
        super(ActionCounterUnique, self).save(*args, **kwargs)

    def increment(self, min=0, max=1):
        return self._change_total(1, min, max)

    def decrement(self, min=0, max=1):
        return self._change_total(-1, min, max)

    def _change_total(self, delta, min, max):
        # TODO: This seems like a race condition. Maybe there's a way to do something like
        # UPDATE actioncounterunique SET total = min(max(field_total+1, min), max) WHERE ...
        # ...and if that's doable, how to detect whether the total changed
        result = (self.total + delta)
        if result > max:
            return False
        if result < min:
            return False
        if result == 0:
            # Don't keep zero entries around in the table.
            self.delete()
        else:
            self.total = F('total') + delta
            self.save()
        return True
