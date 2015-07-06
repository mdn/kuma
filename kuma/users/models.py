import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.db import models
from django.utils.functional import cached_property

from allauth.account.signals import user_signed_up, email_confirmed
from allauth.socialaccount.signals import social_account_removed
from constance import config
from timezones.fields import TimeZoneField
from tower import ugettext_lazy as _
from waffle import switch_is_active

from kuma.core.fields import LocaleField, JSONField
from kuma.core.managers import NamespacedTaggableManager
from kuma.core.models import ModelBase
from kuma.wiki.models import Revision
from kuma.wiki.helpers import wiki_url

from .helpers import gravatar_url
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
    class Meta:
        db_table = 'auth_user'

    @cached_property
    def profile(self):
        """
        Returns site-specific profile for this user. Is locally cached.
        """
        return (UserProfile.objects.using(self._state.db)
                                   .get(user__id__exact=self.id))


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
        return (config.BETA_GROUP_NAME in
                self.user.groups.values_list('name', flat=True))

    @property
    def is_banned(self):
        return self.user.bans.filter(is_active=True).exists()

    def active_ban(self):
        if self.is_banned:
            return self.user.bans.filter(is_active=True)[:1][0]

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


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        p, created = UserProfile.objects.get_or_create(user=instance)


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def invalidate_gravatar_url(sender, instance, created, **kwargs):
    job = UserGravatarURLJob()
    if instance.email:
        job.invalidate(instance.email)
    elif instance.email is None:
        job.delete(instance.email)


@receiver(user_signed_up)
def on_user_signed_up(sender, request, user, **kwargs):
    context = {'request': request}
    msg = _('You have completed the first step of <a href="%s">getting started with MDN</a>') % wiki_url(context, 'MDN/Getting_started')
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
