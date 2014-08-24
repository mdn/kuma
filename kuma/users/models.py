import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.db import models
from django.utils.functional import cached_property

from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import (pre_social_login,
                                           social_account_removed)
import constance.config
from jsonfield import JSONField
from taggit_extras.managers import NamespacedTaggableManager
from timezones.fields import TimeZoneField, MAX_TIMEZONE_LENGTH
from tower import ugettext_lazy as _
from waffle import switch_is_active

from devmo.models import ModelBase
from kuma.wiki.models import Revision
from sumo.models import LocaleField

from .helpers import gravatar_url
from .tasks import send_welcome_email


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
            prefix='https://www.linkedin.com/',
            regex='^https?:\/\/www.linkedin.com\/(in|pub)',
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

    @property
    def gravatar(self):
        return gravatar_url(self.user)

    def allows_editing_by(self, user):
        if user == self.user:
            return True
        if user.is_staff or user.is_superuser:
            return True
        return False

    def wiki_activity(self):
        return (Revision.objects.filter(creator=self.user)
                                .order_by('-created')[:5])


@receiver(models.signals.post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        p, created = UserProfile.objects.get_or_create(user=instance)


@receiver(user_signed_up)
def on_user_signed_up(sender, request, user, **kwargs):
    if switch_is_active('welcome_email'):
        send_welcome_email.delay(user.pk, request.locale)


@receiver(pre_social_login)
def on_pre_social_login(sender, request, sociallogin, **kwargs):
    """
    Invoked just after a user successfully authenticates via a
    social provider, but before the login is actually processed.

    We use it to store the name of the socialaccount provider in
    the user's session.
    """
    if 'sociallogin_provider' not in request.session:
        request.session['sociallogin_provider'] = sociallogin.account.provider
        request.session.modified = True


@receiver(social_account_removed)
def on_social_account_removed(sender, request, socialaccount, **kwargs):
    """
    Invoked just after a user successfully removed a social account

    We use it to reset the name of the socialaccount provider in
    the user's session to one that he also has.
    """
    user = socialaccount.user
    try:
        all_socialaccounts = user.socialaccount_set.all()
        next_socialaccount = all_socialaccounts[0]
        request.session['sociallogin_provider'] = next_socialaccount.provider
        request.session.modified = True
    except (ObjectDoesNotExist, IndexError):
        pass


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
