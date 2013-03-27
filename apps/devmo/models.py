import csv
from datetime import datetime
import time

import urllib2
import urllib
import hashlib

import pytz
from timezones.fields import TimeZoneField, MAX_TIMEZONE_LENGTH

from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.core.cache import cache

import caching.base
import xml.sax
from xml.sax.handler import ContentHandler

import html5lib
from html5lib import sanitizer
from tower import ugettext_lazy as _

from jsonfield import JSONField

from sumo.models import LocaleField
from wiki.models import Revision

from taggit_extras.managers import NamespacedTaggableManager

import south.modelsinspector
south.modelsinspector.add_ignored_fields(["^taggit\.managers"])


DEKIWIKI_ENDPOINT = getattr(settings,
        'DEKIWIKI_ENDPOINT', 'https://developer.mozilla.org')
USER_DOCS_ACTIVITY_FEED_CACHE_PREFIX = getattr(settings,
        'USER_DOCS_ACTIVITY_FEED_CACHE_PREFIX', 'dekiuserdocsfeed')
USER_DOCS_ACTIVITY_FEED_CACHE_TIMEOUT = getattr(settings,
        'USER_DOCS_ACTIVITY_FEED_CACHE_TIMEOUT', 900)
USER_DOCS_ACTIVITY_FEED_TIMEZONE = getattr(settings,
        'USER_DOCS_ACTIVITY_FEED_TIMEZONE', 'America/Phoenix')
DEFAULT_AVATAR = getattr(settings,
        'DEFAULT_AVATAR', settings.MEDIA_URL + 'img/avatar-default.png')


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all MDN models: Implements caching."""

    objects = caching.base.CachingManager()

    class Meta:
        abstract = True


class UserProfile(ModelBase):
    """
    The UserProfile *must* exist for each
    django.contrib.auth.models.User object. This may be relaxed
    once Dekiwiki isn't the definitive db for user info.

    timezone and language fields are syndicated to Dekiwiki
    """

    # Website fields defined for the profile form
    # TODO: Someday this will probably need to allow arbitrary per-profile
    # entries, and these will just be suggestions.
    website_choices = [
        ('website', dict(
            label=_(u'Website'),
            prefix='http://',
            regex='^https?://',
        )),
        ('twitter', dict(
            label=_(u'Twitter'),
            prefix='http://twitter.com/',
            regex='^https?://twitter.com/',
        )),
        ('github', dict(
            label=_(u'GitHub'),
            prefix='http://github.com/',
            regex='^https?://github.com/',
        )),
        ('stackoverflow', dict(
            label=_(u'StackOverflow'),
            prefix='http://stackoverflow.com/users/',
            regex='^https?://stackoverflow.com/users/',
        )),
        ('linkedin', dict(
            label=_(u'LinkedIn'),
            prefix='http://www.linkedin.com/in/',
            regex='^https?://www.linkedin.com/in/',
        )),
    ]

    class Meta:
        db_table = 'user_profiles'

    # This could be a ForeignKey, except wikidb might be
    # a different db
    deki_user_id = models.PositiveIntegerField(default=0,
                                               editable=False)
    timezone = TimeZoneField(null=True, blank=True,
                             verbose_name=_(u'Timezone'))
    locale = LocaleField(null=True, blank=True, db_index=True,
                         verbose_name=_(u'Language'))
    homepage = models.URLField(max_length=255, blank=True, default='',
                               error_messages={
                               'invalid': _(u'This URL has an invalid format. '
                                            u'Valid URLs look like '
                                            u'http://example.com/my_page.')})
    title = models.CharField(_(u'Title'), max_length=255, default='',
                             blank=True)
    fullname = models.CharField(_(u'Name'), max_length=255, default='',
                                blank=True)
    organization = models.CharField(_(u'Organization'), max_length=255,
                                    default='', blank=True)
    location = models.CharField(_(u'Location'), max_length=255, default='',
                                blank=True)
    bio = models.TextField(_(u'About Me'), blank=True)

    irc_nickname = models.CharField(_(u'IRC nickname'), max_length=255,
                                    default='', blank=True)

    tags = NamespacedTaggableManager(_(u'Tags'), blank=True)

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

    @models.permalink
    def get_absolute_url(self):
        return ('devmo.views.profile_view', [self.user.username])

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
        if not settings.DEKIWIKI_ENDPOINT:
            # There is no deki_user, if the MindTouch API is disabled.
            return None
        if not self._deki_user:
            # Need to find the DekiUser corresponding to the ID
            from dekicompat.backends import DekiUserBackend
            self._deki_user = (DekiUserBackend()
                    .get_deki_user(self.deki_user_id))
        return self._deki_user

    def gravatar_url(self, secure=True, size=220, rating='pg',
            default=DEFAULT_AVATAR):
        """Produce a gravatar image URL from email address."""
        base_url = (secure and 'https://secure.gravatar.com' or
            'http://www.gravatar.com')
        m = hashlib.md5(self.user.email.lower().encode('utf8'))
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

    @property
    def mindtouch_language(self):
        if not self.locale:
            return ''
        return settings.LANGUAGE_DEKI_MAP[self.locale]

    @property
    def mindtouch_timezone(self):
        if not self.timezone:
            return ''
        base_seconds = self.timezone._utcoffset.days * 86400
        offset_seconds = self.timezone._utcoffset.seconds
        offset_hours = (base_seconds + offset_seconds) / 3600
        return "%03d:00" % offset_hours

    def save(self, *args, **kwargs):
        skip_mindtouch_put = kwargs.get('skip_mindtouch_put', False)
        if 'skip_mindtouch_put' in kwargs:
            del kwargs['skip_mindtouch_put']
        super(UserProfile, self).save(*args, **kwargs)
        if skip_mindtouch_put:
            return
        if not settings.DEKIWIKI_ENDPOINT:
            # Skip if the MindTouch API is unavailable
            return
        from dekicompat.backends import DekiUserBackend
        DekiUserBackend.put_mindtouch_user(self.user)

    def wiki_activity(self):
        return Revision.objects.filter(
                                    creator=self.user).order_by('-created')[:5]


def create_user_profile(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        p, created = UserProfile.objects.get_or_create(user=instance)

#models.signals.post_save.connect(create_user_profile, sender=DjangoUser)

# from https://github.com/brosner/django-timezones/pull/13
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[(
            (TimeZoneField,),   # Class(es) these apply to
            [],                 # Positional arguments (not used)
            {                   # Keyword argument
            "max_length": ["max_length", {"default": MAX_TIMEZONE_LENGTH}],
            }
            )],
        patterns=['timezones\.fields\.'])
    add_introspection_rules([], ['sumo.models.LocaleField'])
except ImportError:
    pass


class UserDocsActivityFeed(object):
    """Fetches, parses, and caches a user activity feed from Mindtouch"""

    def __init__(self, username, base_url=''):
        self.username = username
        self.base_url = base_url
        self._items = None

    def feed_url_for_user(self):
        """Build the API URL for a user docs activity feed"""
        return u'%s/@api/deki/users/=%s/feed?format=raw' % (
            DEKIWIKI_ENDPOINT, urllib.quote_plus(
                                                self.username.encode('utf-8')))

    def fetch_user_feed(self):
        """Fetch a user feed from DekiWiki"""
        return urllib.urlopen(self.feed_url_for_user()).read()

    @property
    def items(self):
        """On-demand items property, fetches and parses feed data with
        caching"""
        if not settings.DEKIWIKI_ENDPOINT:
            # If there's no MindTouch API, then there's no user feed to fetch.
            # There should be a switch in the view which skips using this feed
            # altogether, but including this skip here just to ensure no
            # attempt is made to call the MT API.
            return []

        # If there's no feed data in the object, try getting it.
        if not self._items:

            try:
                # Try getting the parsed feed data from cache
                url = self.feed_url_for_user()
                cache_key = '%s:%s' % (
                    USER_DOCS_ACTIVITY_FEED_CACHE_PREFIX,
                    hashlib.md5(url).hexdigest())
                items = cache.get(cache_key)

                # If no cached feed data, try fetching & parsing it.
                if not items:
                    data = self.fetch_user_feed()
                    parser = UserDocsActivityFeedParser(base_url=self.base_url)
                    parser.parseString(data)
                    items = parser.items
                    cache.set(cache_key, items,
                              USER_DOCS_ACTIVITY_FEED_CACHE_TIMEOUT)

            except Exception:
                # On error, items isn't just empty, it's False
                items = False

            # We've got feed data now.
            self._items = items

        return self._items


class UserDocsActivityFeedParser(ContentHandler):
    """XML SAX parser for Mindtouch user activity feed.
    eg. https://developer.mozilla.org/@api/deki/users/=Sheppy/feed?format=raw
    <table>
        <change>
            <rc_id>...</rc_id>
            <rc_comment>...</rc_comment>
            ...
        </change>
        <change>
            ...
        </change>
    </table>
    """

    def __init__(self, base_url):
        self.items = []
        self.in_current = False
        self.base_url = base_url

    def parseString(self, data):
        xml.sax.parseString(data, self, self.error)

    def error(self):
        pass

    def startDocument(self):
        self.items = []

    def startElement(self, name, attrs):
        self.cdata = []
        if 'change' == name:
            # <change> is the start of a set of properties, so start blank.
            self.curr = {}
            self.in_current = True

    def characters(self, content):
        self.cdata.append(content)

    def endElement(self, name):
        if 'table' == name:
            # </table> is synonmous with endDocument, so ignore.
            return
        elif 'change' == name:
            # The end of a <change> item signals the completion of collecting
            # a set of properties.
            self.items.append(UserDocsActivityFeedItem(self.curr,
                                                       self.base_url))
            self.in_current = False
        elif self.in_current:
            # Treat child tags of <current> tags as properties to collect
            self.curr[name] = ''.join(self.cdata)
            self.cdata = []

    def endDocument(self):
        pass


class UserDocsActivityFeedItem(object):
    """Wrapper for a user docs activity feed item"""

    # Timestamp is 20110820122346
    RC_TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'

    # This list grabbed from DekiWiki C# source
    # http://mzl.la/mindtouch_data_types
    RC_TYPES = {
        "0": "EDIT",
        "1": "NEW",
        "2": "MOVE",
        "3": "LOG",
        "4": "MOVE_OVER_REDIRECT",
        "5": "PAGEDELETED",
        "6": "PAGERESTORED",
        "7": "COPY",
        "40": "COMMENT_CREATE",
        "41": "COMMENT_UPDATE",
        "42": "COMMENT_DELETE",
        "50": "FILE",
        "51": "PAGEMETA",
        "52": "TAGS",
        "54": "GRANTS_ADDED",
        "55": "GRANTS_REMOVED",
        "56": "RESTRICTION_UPDATED",
        "60": "USER_CREATED",
    }

    # See: http://mzl.la/mindtouch_constants
    # TODO: Merge these dicts to id->prefix?
    RC_NAMESPACE_NAMES = {
        "0": "NS_MAIN",
        "1": "NS_TALK",
        "2": "NS_USER",
        "3": "NS_USER_TALK",
        "4": "NS_PROJECT",
        "5": "NS_PROJECT_TALK",
        "6": "NS_IMAGE",
        "7": "NS_IMAGE_TALK",
        "8": "NS_MEDIAWIKI",
        "9": "NS_MEDIAWIKI_TALK",
        "10": "NS_TEMPLATE",
        "11": "NS_TEMPLATE_TALK",
        "12": "NS_HELP",
        "13": "NS_HELP_TALK",
        "14": "NS_CATEGORY",
        "15": "NS_CATEGORY_TALK",
        "16": "NS_ATTACHMENT",
    }
    RC_NAMESPACE_PREFIXES = {
        "NS_ADMIN": u"Admin",
        "NS_MEDIA": u"Media",
        "NS_SPECIAL": u"Special",
        "NS_MAIN": u"",
        "NS_TALK": u"Talk",
        "NS_USER": u"User",
        "NS_USER_TALK": u"User_talk",
        "NS_PROJECT": u"Project",
        "NS_PROJECT_TALK": u"Project_talk",
        "NS_IMAGE_TALK": u"Image_comments",
        "NS_MEDIAWIKI": u"MediaWiki",
        "NS_TEMPLATE": u"Template",
        "NS_TEMPLATE_TALK": u"Template_talk",
        "NS_HELP": u"Help",
        "NS_HELP_TALK": u"Help_talk",
        "NS_CATEGORY": u"Category",
        "NS_CATEGORY_TALK": u"Category_comments",
        "NS_ATTACHMENT": u"File",
    }

    def __init__(self, data, base_url=''):
        self.__dict__ = data
        self.base_url = base_url

    @property
    def rc_timestamp(self):
        """Parse rc_timestamp into datestamp() with proper time zone"""
        tt = list(time.strptime(self.__dict__['rc_timestamp'],
                                self.RC_TIMESTAMP_FORMAT)[0:6])
        tt.extend([0, pytz.timezone(USER_DOCS_ACTIVITY_FEED_TIMEZONE)])
        return datetime(*tt)

    @property
    def rc_revision(self):
        """Make rc_revision into an int"""
        return int(self.__dict__['rc_revision'])

    @property
    def rc_type(self):
        """Attempt to convert rc_type into a more descriptive name"""
        return self.RC_TYPES.get(self.__dict__['rc_type'], 'UNKNOWN')

    def _add_prefix_to_title(self, title):
        """Mindtouch keeps the prefix text separate from the page title, so
        we'll need to re-add it."""
        ns_id = self.RC_NAMESPACE_NAMES.get(self.rc_namespace, '')
        prefix = self.RC_NAMESPACE_PREFIXES.get(ns_id, '')
        if prefix:
            return u'%s:%s' % (self.RC_NAMESPACE_PREFIXES[ns_id], title)
        else:
            return title

    @property
    def rc_title(self):
        """Include the wiki namespace prefix in the title"""
        title = self.__dict__['rc_title']
        return self._add_prefix_to_title(title)

    @property
    def rc_moved_to_title(self):
        """Include the wiki namespace prefix in the moved-to title"""
        title = self.__dict__['rc_moved_to_title']
        return self._add_prefix_to_title(title)

    @property
    def current_title(self):
        if 'MOVE' == self.rc_type:
            return self.rc_moved_to_title
        else:
            return self.rc_title

    @property
    def view_url(self):
        return u'%s/%s' % (self.base_url, urllib.quote(
                                            self.current_title.encode('utf8')))

    @property
    def edit_url(self):
        if not self.rc_type in ('EDIT', 'MOVE', 'TAGS', 'NEW', 'FILE'):
            return None
        return '%s/index.php?%s' % (self.base_url, urllib.urlencode(dict(
            title=self.current_title.encode('utf8'),
            action='edit',
        )))

    @property
    def history_url(self):
        if not self.rc_type in ('EDIT', 'MOVE', 'TAGS', 'FILE'):
            return None
        return '%s/index.php?%s' % (self.base_url, urllib.urlencode(dict(
            title=self.current_title.encode('utf8'),
            action='history',
        )))

    @property
    def diff_url(self):
        if not self.rc_type in ('EDIT',):
            return None
        if not self.rc_revision > 1:
            return None
        return '%s/index.php?%s' % (self.base_url, urllib.urlencode(dict(
            title=self.current_title.encode('utf8'),
            action='diff',
            revision=self.rc_revision - 1,
            diff=self.rc_revision,
        )))


def parse_date(date_str):
    try:
        parsed_date = datetime.strptime(date_str, "%m/%d/%Y")
        parsed_date.strftime("%Y-%m-%d")
        return parsed_date
    except:
        return None


FIELD_MAP = {
    "date": ["Start Date", None, parse_date],
    "end_date": ["End Date", None, parse_date],
    "conference": ["Conference", None],
    "conference_link": ["Link", None],
    "location": ["Location", None],
    "people": ["Attendees", None],
    "description": ["Description", None],
    "done": ["Done", None],
    "materials": ["Materials URL", None],
}


def parse_header_line(header_line):
    for field_name in FIELD_MAP.keys():
        field = FIELD_MAP[field_name]
        if field[1] == None:
            try:
                FIELD_MAP[field_name][1] = header_line.index(field[0])
            except IndexError:
                FIELD_MAP[field_name][1] = ''
            except ValueError:
                FIELD_MAP[field_name][1] = ''


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

    @classmethod
    def parse_row(cls, doc_row):
        row = {}
        for field_name in FIELD_MAP.keys():
            field = FIELD_MAP[field_name]
            if len(doc_row) > field[1]:
                field_value = doc_row[field[1]]
            else:
                field_value = ''
            if len(field) >= 3 and callable(field[2]):
                field_value = field[2](field_value)
            row[field_name] = field_value
        return row

    def reload(self, data=None):
        events = []
        u = None

        if not data:
            try:
                u = urllib2.urlopen(self.url)
            except Exception:
                return False
        data = csv.reader(u) if u else data
        if not data:
            return False

        events = list(Calendar.as_unicode(data))
        Event.objects.filter(calendar=self).delete()

        # use column indices from header names so re-ordering
        # columns doesn't blow us up
        header_line = events.pop(0)
        parse_header_line(header_line)

        today = datetime.today()

        for event_line in events:
            event = None
            row = Calendar.parse_row(event_line)
            if row['date'] == None:
                continue
            if row['end_date'] == None:
                row['end_date'] = row['date']
            row['done'] = False
            if row['end_date'] < today:
                row['done'] = True
            row['end_date'] = row['end_date'].strftime("%Y-%m-%d")
            row['date'] = row['date'].strftime("%Y-%m-%d")
            for field_name in ('conference', 'location', 'people',
                               'description'):
                # Sometimes we still get here with non-ASCII data;
                # that will blow up on attempting to save, so we check
                # the text-based fields to make sure they decode
                # cleanly as ASCII, and force-decode them as UTF-8 if
                # they don't.
                try:
                    row[field_name].decode('ascii')
                except UnicodeDecodeError:
                    row[field_name] = row[field_name].decode('utf-8', 'ignore')

            try:
                event = Event(calendar=self, **row)
                event.save()
            except:
                continue

    def __unicode__(self):
        return self.shortname


class Event(ModelBase):
    """An event"""

    date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    conference = models.CharField(max_length=255)
    conference_link = models.URLField(blank=True)
    location = models.CharField(max_length=255)
    people = models.TextField()
    description = models.TextField()
    done = models.BooleanField(default=False)
    materials = models.URLField(blank=True)
    calendar = models.ForeignKey(Calendar)

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        return '%s - %s, %s' % (self.date, self.conference, self.location)
