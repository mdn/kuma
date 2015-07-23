import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.db import models
from django.utils.functional import cached_property

from allauth.account.signals import user_signed_up, email_confirmed
from allauth.socialaccount.signals import social_account_removed
from constance import config
from timezones.fields import TimeZoneField
from sundial.zones import COMMON_GROUPED_CHOICES
from tower import ugettext_lazy as _
from waffle import switch_is_active

from kuma.core.fields import LocaleField, JSONField
from kuma.core.managers import NamespacedTaggableManager
from kuma.core.models import ModelBase
from kuma.core.urlresolvers import reverse

from .constants import USERNAME_REGEX
from .jobs import UserGravatarURLJob
from .tasks import send_welcome_email


class UserBan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="bans",
                             verbose_name="Banned user")
    by = models.ForeignKey(settings.AUTH_USER_MODEL,
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


@receiver(models.signals.post_delete,
          sender=UserBan, dispatch_uid='users.user_ban.delete')
def delete_ban(**kwargs):
    ban = kwargs.get('instance', None)
    if ban is not None:
        ban.user.is_active = True
        ban.user.save()


class User(AbstractUser):
    """
    Our custom user class that contains just a link to the user's profile
    right now.
    """
    timezone = models.CharField(
        verbose_name=_(u'Timezone'),
        max_length=42,
        blank=True,
        choices=COMMON_GROUPED_CHOICES,
        default=settings.TIME_ZONE,
    )
    locale = LocaleField(
        verbose_name=_(u'Language'),
        blank=True,
        db_index=True,
    )
    homepage = models.URLField(
        verbose_name=_(u'Homepage'),
        max_length=255,
        blank=True,
        error_messages={
            'invalid': _(u'This URL has an invalid format. '
                         u'Valid URLs look like http://example.com/my_page.')
        },
    )
    title = models.CharField(
        verbose_name=_(u'Title'),
        max_length=255,
        blank=True,
    )
    fullname = models.CharField(
        verbose_name=_(u'Name'),
        max_length=255,
        blank=True,
    )
    organization = models.CharField(
        verbose_name=_(u'Organization'),
        max_length=255,
        blank=True,
    )
    location = models.CharField(
        verbose_name=_(u'Location'),
        max_length=255,
        blank=True,
    )
    bio = models.TextField(
        verbose_name=_(u'About Me'),
        blank=True,
    )
    irc_nickname = models.CharField(
        verbose_name=_(u'IRC nickname'),
        max_length=255,
        blank=True,
    )

    tags = NamespacedTaggableManager(verbose_name=_(u'Tags'), blank=True)

    # should this user receive contentflagging emails?
    content_flagging_email = models.BooleanField(default=False)

    WEBSITE_VALIDATORS = {
        'website': validators.RegexValidator(
            r'^https?://',
            _('Enter a valid website URL.'),
            'invalid',
        ),
        'twitter': validators.RegexValidator(
            r'^https?://twitter\.com/',
            _('Enter a valid Twitter URL.'),
            'invalid',
        ),
        'github': validators.RegexValidator(
            r'^https?://github\.com/',
            _('Enter a valid GitHub URL.'),
            'invalid',
        ),
        'stackoverflow': validators.RegexValidator(
            r'^https?://stackoverflow\.com/users/',
            _('Enter a valid Stack Overflow URL.'),
            'invalid',
        ),
        'linkedin': validators.RegexValidator(
            r'^https?://((www|\w\w)\.)?linkedin.com/((in/[^/]+/?)|(pub/[^/]+/((\w|\d)+/?){3}))$',
            _('Enter a valid LinkedIn URL.'),
            'invalid',
        ),
        'mozillians': validators.RegexValidator(
            r'^https?://mozillians\.org/u/',
            _('Enter a valid Mozillians URL.'),
            'invalid',
        ),
        'facebook': validators.RegexValidator(
            r'^https?://www\.facebook\.com/',
            _('Enter a valid Facebook URL.'),
            'invalid',
        )
    }

    # a bunch of user URLs
    website_url = models.TextField(
        _(u'Website'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['website']],
    )
    mozillians_url = models.TextField(
        _(u'Mozillians'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['mozillians']],
    )
    github_url = models.TextField(
        _(u'GitHub'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['github']],
    )
    twitter_url = models.TextField(
        _(u'Twitter'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['twitter']],
    )
    linkedin_url = models.TextField(
        _(u'LinkedIn'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['linkedin']],
    )
    facebook_url = models.TextField(
        _(u'Facebook'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['facebook']],
    )
    stackoverflow_url = models.TextField(
        _(u'Stack Overflow'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['stackoverflow']],
    )

    class Meta:
        db_table = 'auth_user'

    @property
    def has_legacy_username(self):
        return not USERNAME_REGEX.search(self.username)

    @cached_property
    def is_beta_tester(self):
        return (config.BETA_GROUP_NAME in
                self.groups.values_list('name', flat=True))

    @cached_property
    def active_ban(self):
        """
        Returns the first active ban for the user or None.
        """
        return self.bans.filter(is_active=True).first()

    def wiki_revisions(self, count=5):
        return (self.created_revisions.prefetch_related('document')
                                      .defer('content', 'summary')
                                      .order_by('-created')[:count])

    def allows_editing_by(self, user):
        return user.is_staff or user.is_superuser or user.pk == self.pk


class UserProfile(ModelBase):
    """
    The UserProfile *must* exist for each
    django.contrib.auth.models.User object. This may be relaxed
    once Dekiwiki isn't the definitive db for user info.

    timezone and language fields are syndicated to Dekiwiki
    """
    # This could be a ForeignKey, except wikidb might be
    # a different db
    deki_user_id = models.PositiveIntegerField(default=0,
                                               editable=False)
    timezone = TimeZoneField(null=True, blank=True,
                             verbose_name=_(u'Timezone'))
    locale = LocaleField(null=True, blank=True, db_index=True,
                         verbose_name=_(u'Language'))
    homepage = models.URLField(
        max_length=255, blank=True, default='',
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             null=True, editable=False, blank=True)

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

    class Meta:
        db_table = 'user_profiles'

    def __unicode__(self):
        return '%s: %s' % (self.id, self.deki_user_id)

    def get_absolute_url(self):
        return self.user.get_absolute_url()


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def invalidate_gravatar_url(sender, instance, created, **kwargs):
    job = UserGravatarURLJob()
    if instance.email:
        handler = job.invalidate
    elif instance.email is None:
        handler = job.delete
    else:
        return
    # do the heavy-lifting for all avatar sizes
    for size in settings.AVATAR_SIZES:
        handler(instance.email, size=size)


@receiver(user_signed_up)
def on_user_signed_up(sender, request, user, **kwargs):
    url = reverse('wiki.document', args=['MDN/Getting_started'])
    msg = _('You have completed the first step of '
            '<a href="%s">getting started with MDN</a>') % url
    messages.success(request, msg)
    if switch_is_active('welcome_email'):
        # only send if the user has already verified at least one email address
        if user.emailaddress_set.filter(verified=True).exists():
            send_welcome_email.delay(user.pk, request.locale)


@receiver(email_confirmed)
def on_email_confirmed(sender, request, email_address, **kwargs):
    if switch_is_active('welcome_email'):
        # only send if the user has exactly one verified (the given)
        # email address, in other words if it was just confirmed
        if not (email_address.user
                             .emailaddress_set.exclude(pk=email_address.pk)
                                              .exists()):
            send_welcome_email.delay(email_address.user.pk, request.locale)


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
