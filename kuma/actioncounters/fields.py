"""Fields for action counters

See also: djangoratings for inspiration
"""
from django.conf import settings
from django.db import models
from django.db.models import F


RECENT_PERIOD = getattr(settings, 'ACTION_COUNTER_RECENT_PERIOD', 60 * 60 * 24)


class ActionCounterField(models.IntegerField):
    """An action counter field contributes two columns to the model - one for
    the current total count, and another for a recent history window count."""

    def __init__(self, *args, **kwargs):

        self.max_total_per_unique = kwargs.pop('max_total_per_unique', 1)
        self.min_total_per_unique = kwargs.pop('min_total_per_unique', 0)

        super(ActionCounterField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        self.name = name

        self.total_field = models.IntegerField(editable=False, default=0,
                                               blank=True, db_index=True)
        cls.add_to_class('%s_total' % (self.name,), self.total_field)

        self.recent_field = models.IntegerField(editable=False, default=0,
                                                blank=True, db_index=True)
        cls.add_to_class('%s_recent' % (self.name,), self.recent_field)

        # TODO: Could maybe include a JSON-formatted history list of recent rollups

        t = ActionCounterCreator(self)
        setattr(cls, name, t)

    def get_db_prep_save(self, value, connection):
        pass


class ActionCounterCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)

    def __get__(self, instance, type=None):
        if instance is None:
            return self.field
        return ActionCounterManager(instance, self.field)

    def __set__(self, instance, value):
        raise TypeError("%s cannot be set directly")


class ActionCounterManager(object):

    def __init__(self, instance, field):
        self.content_type = None
        self.instance = instance
        self.field = field
        self.name = field.name

        self.total_field_name = "%s_total" % (self.name,)
        self.recent_field_name = "%s_recent" % (self.name,)

    def _get_total(self, default=0):
        return getattr(self.instance, self.total_field_name, default)

    def _set_total(self, value):
        return setattr(self.instance, self.total_field_name, value)

    total = property(_get_total, _set_total)

    def _get_recent(self, default=0):
        return getattr(self.instance, self.recent_field_name, default)

    def _set_recent(self, value):
        return setattr(self.instance, self.recent_field_name, value)

    recent = property(_get_recent, _set_recent)

    def _get_counter_for_request(self, request, do_create=True):
        from .models import ActionCounterUnique
        counter, created = ActionCounterUnique.objects.get_unique_for_request(
            self.instance, self.name, request, do_create)
        return counter

    def get_total_for_request(self, request):
        counter = self._get_counter_for_request(request, False)
        return counter and counter.total or 0

    def increment(self, request):
        counter = self._get_counter_for_request(request)
        ok = counter.increment(
            self.field.min_total_per_unique,
            self.field.max_total_per_unique)
        if ok:
            self._change_total(1)

    def decrement(self, request):
        counter = self._get_counter_for_request(request)
        ok = counter.decrement(
            self.field.min_total_per_unique,
            self.field.max_total_per_unique)
        if ok:
            self._change_total(-1)

    def _change_total(self, delta):
        # This is ugly, but results in a single-column UPDATE like so:
        #
        # UPDATE `actioncounters_testmodel`
        # SET `likes_total` = `actioncounters_testmodel`.`likes_total` + 1
        # WHERE `actioncounters_testmodel`.`id` = 1
        #
        # This also avoids updating datestamps and doing a more verbose query.
        # TODO: Find a less-ugly way to do this.
        m_cls = self.instance.__class__
        qs = m_cls.objects.all().filter(pk=self.instance.pk)
        update_kwargs = {
            "%s" % self.total_field_name: F(self.total_field_name) + delta
        }
        qs.update(**update_kwargs)

        # HACK: This value change is just for the benefit of local code,
        # may possibly fall out of sync with the actual database if there's a
        # race condition. A subsequent save() could clobber concurrent counter
        # changes.
        self.total = self.total + delta
