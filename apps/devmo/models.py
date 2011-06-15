import logging

from django.db import models

from django.contrib.auth.models import User as DjangoUser

import caching.base

from tower import ugettext as _

class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all MDN models: Implements caching."""

    objects = caching.base.CachingManager()

    class Meta:
        abstract = True

class UserProfile(ModelBase):
    """
    Want to track some data that isn't in dekiwiki's db?
    This is the proper grab bag for user profile info.

    Also, dekicompat middleware and backends use this
    class to find Django user objects.

    The UserProfile *must* exist for each
    django.contrib.auth.models.User object. This may be relaxed
    once Dekiwiki isn't the definitive db for user info.
    """
    # This could be a ForeignKey, except wikidb might be
    # a different db
    deki_user_id = models.PositiveIntegerField(default=0,
                                               editable=False)
    homepage = models.URLField(max_length=255, blank=True, default='',
                               verify_exists=False, error_messages={
                               'invalid': _('This URL has an invalid format. '
                                            'Valid URLs look like '
                                            'http://example.com/my_page.')})
    # Duplicates phpBB's location field, but it's days are numbered
    location = models.CharField(max_length=255, default='', blank=True)
    # should this user receive contentflagging emails?
    content_flagging_email = models.BooleanField(default=False)
    user = models.ForeignKey(DjangoUser, null=True, editable=False, blank=True)

    class Meta:
        db_table = 'user_profiles'

    def __unicode__(self):
        return '%s: %s' % (self.id, self.deki_user_id)

    def __getattr__(self, name):
        if not 'deki_user_id' in self.__dict__:
            raise AttributeError
        if not 'deki_user' in self.__dict__:
            from dekicompat.backends import DekiUserBackend
            self.__dict__['deki_user'] = \
                DekiUserBackend().get_deki_user(self.__dict__['deki_user_id'])
        if hasattr(self.__dict__['deki_user'], name):
            return getattr(self.__dict__['deki_user'], name)
        raise AttributeError

