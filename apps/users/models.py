import datetime
import urllib
import hashlib

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.functional import cached_property

import constance.config
from jsonfield import JSONField
from taggit_extras.managers import NamespacedTaggableManager
from timezones.fields import TimeZoneField, MAX_TIMEZONE_LENGTH
from tower import ugettext_lazy as _

from devmo.models import ModelBase
from sumo.models import LocaleField
from wiki.models import Revision

DEFAULT_AVATAR = getattr(settings, 'DEFAULT_AVATAR',
                         settings.MEDIA_URL + 'img/avatar-default.png')


class UserBan(models.Model):
    user = models.ForeignKey(User,
                             related_name="bans",
                             verbose_name="Banned user")
    by = models.ForeignKey(User,
                           related_name="bans_issued",
                           verbose_name="Banned by")
    reason = models.TextField()
    date = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True, help_text="(Is ban active)")

    def __unicode__(self):
        message = _(u'%s banned by %s') % (self.user, self.by)
        if not self.is_active:
            message = _(u"%s (no longer active)") % message
        return message

    def save(self, *args, **kwargs):
        super(UserBan, self).save(*args, **kwargs)
        self.user.is_active = not self.is_active
        self.user.save()


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
            fa_icon='icon-link',
        )),
        ('twitter', dict(
            label=_(u'Twitter'),
            prefix='https://twitter.com/',
            regex='^https?://twitter.com/',
            fa_icon='icon-twitter',
        )),
        ('github', dict(
            label=_(u'GitHub'),
            prefix='https://github.com/',
            regex='^https?://github.com/',
            fa_icon='icon-github',
        )),
        ('stackoverflow', dict(
            label=_(u'Stack Overflow'),
            prefix='https://stackoverflow.com/users/',
            regex='^https?://stackoverflow.com/users/',
            fa_icon='icon-stackexchange',
        )),
        ('linkedin', dict(
            label=_(u'LinkedIn'),
            prefix='https://www.linkedin.com/in/',
            regex='^https?://www.linkedin.com/in/',
            fa_icon='icon-linkedin',
        )),
        ('mozillians', dict(
            label=_(u'Mozillians'),
            prefix='https://mozillians.org/u/',
            regex='^https?://mozillians.org/u/',
            fa_icon='icon-group',
        )),
        ('facebook', dict(
            label=_(u'Facebook'),
            prefix='https://www.facebook.com/',
            regex='^https?://www.facebook.com/',
            fa_icon='icon-facebook',
        ))
    ]
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
    user = models.ForeignKey(User, null=True, editable=False, blank=True)

    # HACK: Grab-bag field for future expansion in profiles
    # We can store arbitrary data in here and later migrate to relational
    # tables if the data ever needs to be indexed & queried. Otherwise,
    # this keeps things nicely denormalized. Ideally, access to this field
    # should be gated through accessors on the model to make that transition
    # easier.
    misc = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __unicode__(self):
        return '%s: %s' % (self.id, self.deki_user_id)

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    @property
    def websites(self):
        if 'websites' not in self.misc:
            self.misc['websites'] = {}
        return self.misc['websites']

    @websites.setter
    def websites(self, value):
        self.misc['websites'] = value

    @cached_property
    def beta_tester(self):
        return (constance.config.BETA_GROUP_NAME in
                self.user.groups.values_list('name', flat=True))

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

    @property
    def small_gravatar(self):
        return self.gravatar_url(size=34)

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

    def wiki_activity(self):
        return (Revision.objects.filter(creator=self.user)
                                .order_by('-created')[:5])


def create_user_profile(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        p, created = UserProfile.objects.get_or_create(user=instance)

# models.signals.post_save.connect(create_user_profile, sender=User)

# from https://github.com/brosner/django-timezones/pull/13
try:
    from south.modelsinspector import (add_introspection_rules,
                                       add_ignored_fields)
    add_ignored_fields(["^taggit\.managers"])
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
