

import datetime

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

import kuma.users.basket as basket
from kuma.core.managers import NamespacedTaggableManager
from kuma.core.urlresolvers import reverse

from .constants import USERNAME_REGEX


class UserBan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="bans",
                             verbose_name="Banned user",
                             on_delete=models.CASCADE)
    by = models.ForeignKey(settings.AUTH_USER_MODEL,
                           related_name="bans_issued",
                           verbose_name="Banned by",
                           on_delete=models.PROTECT)
    reason = models.TextField()
    date = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True, help_text="(Is ban active)")

    def __str__(self):
        message = _('%(banned_user)s banned by %(banned_by)s') % {
            'banned_user': self.user, 'banned_by': self.by}
        if not self.is_active:
            message = _('%s (no longer active)') % message
        return message


class User(AbstractUser):
    """
    Our custom user class.
    """
    timezone = models.CharField(
        verbose_name=_('Timezone'),
        max_length=42,
        blank=True,
        default=settings.TIME_ZONE,
        # Note the deliberate omission of the `choices=` here.
        # That's because there's no good way to list all possible
        # timezones as a 2-D tuple. The *name* of the timezone rarely
        # changes but the human-friendly description of it easily does.
    )
    locale = models.CharField(
        max_length=7,
        default=settings.LANGUAGE_CODE,
        choices=settings.SORTED_LANGUAGES,
        verbose_name=_('Language'),
        blank=True,
        db_index=True,
    )
    homepage = models.URLField(
        verbose_name=_('Homepage'),
        max_length=255,
        blank=True,
        error_messages={
            'invalid': _('This URL has an invalid format. '
                         'Valid URLs look like http://example.com/my_page.')
        },
    )
    title = models.CharField(
        verbose_name=_('Title'),
        max_length=255,
        blank=True,
    )
    fullname = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        blank=True,
    )
    organization = models.CharField(
        verbose_name=_('Organization'),
        max_length=255,
        blank=True,
    )
    location = models.CharField(
        verbose_name=_('Location'),
        max_length=255,
        blank=True,
    )
    bio = models.TextField(
        verbose_name=_('About Me'),
        blank=True,
    )
    irc_nickname = models.CharField(
        verbose_name=_('IRC nickname'),
        max_length=255,
        blank=True,
    )

    salesforce_connection = models.CharField(
        choices=[(c, c) for c in ('', 'pending', 'success', 'error')],
        default='',
        max_length=10,
        blank=True
    )

    tags = NamespacedTaggableManager(verbose_name=_('Tags'), blank=True)

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
            r'^https?://([a-z]{2}\.)?stackoverflow\.com/users/',
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
        ),
        'discourse': validators.RegexValidator(
            r'^https://discourse\.mozilla\.org/u/',
            _('Enter a valid Discourse URL.'),
            'invalid',
        )
    }

    # a bunch of user URLs
    website_url = models.TextField(
        _('Website'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['website']],
    )
    mozillians_url = models.TextField(
        _('Mozillians'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['mozillians']],
    )
    github_url = models.TextField(
        _('GitHub'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['github']],
    )
    is_github_url_public = models.BooleanField(
        _('Public GitHub URL'),
        default=False,
    )
    twitter_url = models.TextField(
        _('Twitter'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['twitter']],
    )
    linkedin_url = models.TextField(
        _('LinkedIn'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['linkedin']],
    )
    facebook_url = models.TextField(
        _('Facebook'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['facebook']],
    )
    stackoverflow_url = models.TextField(
        _('Stack Overflow'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['stackoverflow']],
    )
    discourse_url = models.TextField(
        _('Discourse'),
        blank=True,
        validators=[WEBSITE_VALIDATORS['discourse']],
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True
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
        """Creates a recovery URL for the user."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        link = reverse('users.recover',
                       kwargs={'token': token, 'uidb64': uidb64})
        return link

    def save(self, *args, **kwargs):
        old_salesforce_connection = (
            User.objects.values_list('salesforce_connection', flat=True).get(pk=self.pk)
            if self.pk
            else ''
        )
        can_connect_to_salesforce = old_salesforce_connection in ('', 'error')
        super().save(*args, **kwargs)
        if self.salesforce_connection == 'pending' and can_connect_to_salesforce:
            basket.subscribe.delay(self.pk, self.email, self.username, self.locale)
