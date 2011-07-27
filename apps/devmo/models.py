import csv
from datetime import datetime

import logging
import urllib2
import urllib
import hashlib

from django.contrib.auth.models import User as DjangoUser
from django.db import models

import caching.base
import html5lib
from html5lib import sanitizer
from tower import ugettext as _

from jsonfield import JSONField

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

import south.modelsinspector
south.modelsinspector.add_ignored_fields(["^taggit\.managers"])


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

    # Website fields defined for the profile form
    # TODO: Someday this will probably need to allow arbitrary per-profile
    # entries, and these will just be suggestions.
    website_choices = [
        ('website', dict(
            label=_('Website'),
            prefix='http://',
        )),
        ('twitter', dict(
            label=_('Twitter'),
            prefix='http://twitter.com/',
        )),
        ('github', dict(
            label=_('GitHub'),
            prefix='http://github.com/',
        )),
        ('stackoverflow', dict(
            label=_('StackOverflow'),
            prefix='http://stackoverflow.com/users/',
        )),
        ('linkedin', dict(
            label=_('LinkedIn'),
            prefix='http://www.linkedin.com/in/',
        )),
    ]

    class Meta:
        db_table = 'user_profiles'

    # This could be a ForeignKey, except wikidb might be
    # a different db
    deki_user_id = models.PositiveIntegerField(default=0,
                                               editable=False)
    homepage = models.URLField(max_length=255, blank=True, default='',
                               verify_exists=False, error_messages={
                               'invalid': _('This URL has an invalid format. '
                                            'Valid URLs look like '
                                            'http://example.com/my_page.')})
    title = models.CharField(_('Title'), max_length=255, default='',
                             blank=True)
    fullname = models.CharField(_('Name'), max_length=255, default='',
                                blank=True)
    organization = models.CharField(_('Organization'), max_length=255,
                                    default='', blank=True)
    location = models.CharField(_('Location'), max_length=255, default='',
                                blank=True)
    bio = models.TextField(_('About Me'), blank=True)
    interests = TaggableManager(_('Interests'), blank=True)

    # should this user receive contentflagging emails?
    content_flagging_email = models.BooleanField(default=False)
    user = models.ForeignKey(DjangoUser, null=True, editable=False, blank=True)

    # HACK: Grab-bag field for future expansion in profiles
    # We can store arbitrary data in here and later migrate to relational
    # tables if the data ever needs to be indexed & queried. Otherwise,
    # this keeps things nicely denormalized. Ideally, access to this field
    # should be gated through accessors on the model to make that transition
    # easier.
    misc = JSONField(blank=True, null=True)

    @property
    def websites(self):
        if 'websites' not in self.misc:
            self.misc['websites'] = {}
        return self.misc['websites']

    @websites.setter
    def websites(self, value):
        self.misc['websites'] = value

    _deki_user = None

    @property
    def deki_user(self):
        if not self._deki_user:
            # Need to find the DekiUser corresponding to the ID
            from dekicompat.backends import DekiUserBackend
            self._deki_user = (DekiUserBackend()
                    .get_deki_user(self.deki_user_id))
        return self._deki_user

    def gravatar_url(self, secure=True, size=220, rating='pg',
            default='http://developer.mozilla.org/media/img/avatar.png'):
        """Produce a gravatar image URL from email address."""
        base_url = (secure and 'https://secure.gravatar.com' or
            'http://www.gravatar.com')
        m = hashlib.md5(self.user.email)
        return '%(base_url)s/avatar/%(hash)s?%(params)s' % dict(
            base_url=base_url, hash=m.hexdigest(),
            params=urllib.urlencode(dict(
                s=size, d=default, r=rating
            ))
        )

    @property
    def gravatar(self):
        return self.gravatar_url()

    def __unicode__(self):
        return '%s: %s' % (self.id, self.deki_user_id)

    def allows_editing_by(self, user):
        if user == self.user:
            return True
        if user.is_staff or user.is_superuser:
            return True
        return False


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
            if event_line[1] != "Conference":
                # verify date string conversion before adding the event
                try:
                    event_date = datetime.strptime(event_line[9], "%m/%d/%Y")
                    event_date_string = event_date.strftime("%Y-%m-%d")
                except:
                    continue
                if len(event_line) > 10:
                    try:
                        event_end_date = datetime.strptime(event_line[10],
                                                           "%m/%d/%Y")
                        event_end_date_string = event_end_date.strftime(
                                                           "%Y-%m-%d")
                    except:
                        event_end_date = None
                event = Event(date=event_date,
                              end_date=event_end_date,
                              conference=event_line[1],
                              conference_link=event_line[3],
                              location=event_line[2], people=event_line[5],
                              description=event_line[6][:255],
                              done=done, calendar=self)
                if len(event_line) > 8:
                    event.materials = event_line[8]
                event.save()

    def __unicode__(self):
        return self.shortname


class Event(ModelBase):
    """An event"""

    date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    conference = models.CharField(max_length=255)
    conference_link = models.URLField(blank=True, verify_exists=False)
    location = models.CharField(max_length=255)
    people = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    done = models.BooleanField(default=False)
    materials = models.URLField(blank=True, verify_exists=False)
    calendar = models.ForeignKey(Calendar)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        return '%s - %s, %s' % (self.date, self.conference, self.location)
