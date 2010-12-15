import datetime
import hashlib
import random
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string

from timezones.fields import TimeZoneField
from tower import ugettext as _
from tower import ugettext_lazy as _lazy

from countries import COUNTRIES
from sumo.models import ModelBase
from sumo.urlresolvers import reverse


SHA1_RE = re.compile('^[a-f0-9]{40}$')


class Profile(ModelBase):
    """Profile model for django users, get it with user.get_profile()."""

    user = models.OneToOneField(User, primary_key=True,
                                verbose_name=_lazy(u'User'))
    name = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_lazy(u'Display name'))
    public_email = models.BooleanField(  # show/hide email
        default=False, verbose_name=_lazy(u'Make my email public'))
    avatar = models.ImageField(upload_to=settings.USER_AVATAR_PATH, null=True,
                               blank=True, verbose_name=_lazy(u'Avatar'),
                               max_length=settings.MAX_FILEPATH_LENGTH)
    bio = models.TextField(null=True, blank=True,
                           verbose_name=_lazy(u'Biography'))
    website = models.URLField(max_length=255, null=True, blank=True,
                              verify_exists=False,
                              verbose_name=_lazy(u'Website'))
    twitter = models.URLField(max_length=255, null=True, blank=True,
                              verify_exists=False,
                              verbose_name=_lazy(u'Twitter URL'))
    facebook = models.URLField(max_length=255, null=True, blank=True,
                               verify_exists=False,
                               verbose_name=_lazy(u'Facebook URL'))
    irc_handle = models.CharField(max_length=255, null=True, blank=True,
                                  verbose_name=_lazy(u'IRC nickname'))
    timezone = TimeZoneField(null=True, blank=True,
                             verbose_name=_lazy(u'Timezone'))
    country = models.CharField(max_length=2, choices=COUNTRIES, null=True,
                               blank=True, verbose_name=_lazy(u'Country'))
    # No city validation
    city = models.CharField(max_length=255, null=True, blank=True,
                            verbose_name=_lazy(u'City'))
    livechat_id = models.CharField(default=None, null=True, blank=True,
                                   max_length=255,
                                   verbose_name=_lazy(u'Livechat ID'))

    def __unicode__(self):
        return unicode(self.user)


# Registration model and manager:
# (based on http://bitbucket.org/ubernostrum/django-registration)
class RegistrationManager(models.Manager):
    """
    Custom manager for the ``RegistrationProfile`` model.

    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired inactive accounts.
    """
    def activate_user(self, activation_key):
        """
        Validate an activation key and activate the corresponding
        ``User`` if valid.

        If the key is valid and has not expired, return the ``User``
        after activating.

        If the key is not valid or has expired, return ``False``.

        If the key is valid but the ``User`` is already active,
        return ``False``.

        To prevent reactivation of an account which has been
        deactivated by site administrators, the activation key is
        reset to the string ``ALREADY_ACTIVATED`` after successful
        activation.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = self.model.ACTIVATED
                profile.save()
                return user
        return False

    def create_inactive_user(self, username, password, email):
        """
        Create a new, inactive ``User`` and ``Profile``, generates a
        ``RegistrationProfile`` and email its activation key to the
        ``User``, returning the new ``User``.
        """
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        new_user.save()
        Profile.objects.create(user=new_user)

        registration_profile = self.create_profile(new_user)

        self.send_confirmation_email(registration_profile)

        return new_user

    def send_confirmation_email(self, registration_profile):
        """Send the user confirmation email."""
        current_site = Site.objects.get_current()
        subject = _('Please confirm your email address')
        url = reverse('users.activate',
                      args=[registration_profile.activation_key])
        message = render_to_string(
            'users/email/activate.ltxt',
            {'activation_key': registration_profile.activation_key,
             'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
             'domain': current_site.domain,
             'activate_url': url})
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                  [registration_profile.user.email])

    def create_profile(self, user):
        """
        Create a ``RegistrationProfile`` for a given
        ``User``, and return the ``RegistrationProfile``.

        The activation key for the ``RegistrationProfile`` will be a
        SHA1 hash, generated from a combination of the ``User``'s
        username and a random salt.
        """
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt + user.username).hexdigest()
        return self.create(user=user,
                           activation_key=activation_key)

    def delete_expired_users(self):
        """
        Remove expired instances of ``RegistrationProfile``.

        Accounts to be deleted are identified by searching for
        instances of ``RegistrationProfile`` with expired activation
        keys, and then checking to see if their associated ``User``
        instances have the field ``is_active`` set to ``False``; any
        ``User`` who is both inactive and has an expired activation
        key will be deleted.
        """
        for profile in self.all():
            if profile.activation_key_expired():
                profile.delete()
                # TODO: We need to limit non-active users actions to just
                # asking a question (no posting to forums, etc.). Then
                # we can safely delete them here to free up the usernames.
                #user = profile.user
                #if not user.is_active:
                #    user.delete()


class RegistrationProfile(models.Model):
    """
    A simple profile which stores an activation key for use during
    user account registration.

    Generally, you will not want to interact directly with instances
    of this model; the provided manager includes methods
    for creating and activating new accounts.
    """
    ACTIVATED = u"ALREADY_ACTIVATED"

    user = models.ForeignKey(User, unique=True, verbose_name=_lazy(u'user'))
    activation_key = models.CharField(verbose_name=_lazy(u'activation key'),
                                      max_length=40)

    objects = RegistrationManager()

    class Meta:
        verbose_name = _lazy(u'registration profile')
        verbose_name_plural = _lazy(u'registration profiles')

    def __unicode__(self):
        return u"Registration information for %s" % self.user

    def activation_key_expired(self):
        """
        Determine whether this ``RegistrationProfile``'s activation
        key has expired, returning a boolean -- ``True`` if the key
        has expired.

        Key expiration is determined by a two-step process:
        1. If the user has already activated, the key will have been
           reset to the string ``ALREADY_ACTIVATED``. Re-activating is
           not permitted, and so this method returns ``True`` in this
           case.
        2. Otherwise, the date the user signed up is incremented by
           the number of days specified in the setting
           ``ACCOUNT_ACTIVATION_DAYS`` (which should be the number of
           days after signup during which a user is allowed to
           activate their account); if the result is less than or
           equal to the current date, the key has expired and this
           method returns ``True``.
        """
        exp_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return (self.activation_key == self.ACTIVATED or
               (self.user.date_joined + exp_date <= datetime.datetime.now()))
    activation_key_expired.boolean = True
