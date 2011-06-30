import csv
import logging
import urllib2

from django.contrib.auth.models import User as DjangoUser
from django.db import models

import caching.base
import html5lib
from html5lib import sanitizer
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


class Calendar(ModelBase):
    """The Calendar spreadsheet"""

    shortname = models.CharField(max_length=255)
    url = models.URLField(
        help_text='URL of the google doc spreadsheet for events', unique=True)

    @classmethod
    def as_unicode(cls, events):
        p = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
        for row in events:
            for idx, cell in enumerate(row):
                row[idx] = p.parseFragment(unicode(cell, 'utf-8')).toxml()
            yield row

    def reload(self, data=None):
        events = []
        u = None
        if not data:
            try:
                u = urllib2.urlopen(self.url)
            except Exception, e:
                return False
        data = csv.reader(u) if u else data
        if not data:
            return False
        events = list(Calendar.as_unicode(data))
        Event.objects.filter(calendar=self).delete()
        for event_line in events:
            event = None
            if len(event_line) > 7:
                done = event_line[7] == 'yes'
            event = Event(date=event_line[4], conference=event_line[1],
                          conference_link=event_line[3],
                          location=event_line[2], people=event_line[5],
                          description=event_line[6][:255], done=done, calendar=self)
            if len(event_line) > 8:
                event.materials = event_line[8]
            if event.conference != "Conference":
                event.save()

    def __unicode__(self):
        return self.shortname


class Event(ModelBase):
    """An event"""

    date = models.CharField(max_length=255)
    conference = models.CharField(max_length=255)
    conference_link = models.URLField(blank=True, verify_exists=False)
    location = models.CharField(max_length=255)
    people = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    done = models.BooleanField(default=False)
    materials = models.URLField(blank=True, verify_exists=False)
    calendar = models.ForeignKey(Calendar)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return '%s - %s, %s' % (self.date, self.conference, self.location)
