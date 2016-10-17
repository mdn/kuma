import datetime
import uuid

from constance import config
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core import validators
from django.db import models
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from sundial.zones import COMMON_GROUPED_CHOICES

from kuma.core.managers import NamespacedTaggableManager
from kuma.core.urlresolvers import reverse

from .constants import USERNAME_REGEX


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
        message = _(u'%(banned_user)s banned by %(banned_by)s') % {
            'banned_user': self.user, 'banned_by': self.by}
        if not self.is_active:
            message = _(u'%s (no longer active)') % message
        return message


class User(AbstractUser):
    """
    Our custom user class.
    """
    timezone = models.CharField(
        verbose_name=_(u'Timezone'),
        max_length=42,
        blank=True,
        choices=COMMON_GROUPED_CHOICES,
        default=settings.TIME_ZONE,
    )
    locale = models.CharField(
        max_length=7,
        default=settings.LANGUAGE_CODE,
        choices=settings.LANGUAGES,
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
                                      .order_by('-id')[:count])

    def allows_editing_by(self, user):
        return user.is_staff or user.is_superuser or user.pk == self.pk

    def get_recovery_url(self):
        """
        Creates a recovery URL for the user.

        The recovery URL uses the password reset workflow, which requires the
        user has a password on their account.  Users without a password get a
        randomly generated password.
        """
        if not self.has_usable_password():
            self.set_password(uuid.uuid4().hex)
            self.save()
        uidb64 = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        link = reverse('users.recover',
                       kwargs={'token': token, 'uidb64': uidb64},
                       force_locale=True)
        return link
