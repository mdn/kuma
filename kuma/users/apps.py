from django.conf import settings
from django.contrib import messages
from django.contrib.auth.apps import AuthConfig
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from allauth.account.signals import user_signed_up, email_confirmed
from allauth.socialaccount.signals import social_account_removed
from waffle import switch_is_active

from kuma.core.urlresolvers import reverse

from .jobs import UserGravatarURLJob
from .tasks import send_welcome_email


class UserConfig(AuthConfig):
    """
    The Django App Config class to store information about the users app
    and do startup time things.
    """
    name = 'kuma.users'
    verbose_name = _('User')

    def ready(self):
        super(UserConfig, self).ready()

        # the user signal handlers to connect to
        User = self.get_model('User')
        signals.post_save.connect(self.on_user_save,
                                  sender=User,
                                  dispatch_uid='users.user.post_save')
        user_signed_up.connect(self.on_user_signed_up)
        email_confirmed.connect(self.on_email_confirmed)
        social_account_removed.connect(self.on_social_account_removed)

        # the user ban signal handlers to connect to
        UserBan = self.get_model('UserBan')
        signals.post_save.connect(self.on_ban_save,
                                  sender=UserBan,
                                  dispatch_uid='users.user_ban.save')
        signals.post_delete.connect(self.on_ban_delete,
                                    sender=UserBan,
                                    dispatch_uid='users.user_ban.delete')

    def on_user_save(self, sender, instance, created, **kwargs):
        """
        A signal handler to be called after saving a user.

        Invalidates the cache for the given user's gravatar URL.
        """
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

    def on_user_signed_up(self, sender, request, user, **kwargs):
        """
        Signal handler to be called when a given user has signed up.
        """
        url = reverse('wiki.document', args=['MDN/Getting_started'])
        msg = _('You have completed the first step of '
                '<a href="%s">getting started with MDN</a>') % url
        messages.success(request, msg)
        if switch_is_active('welcome_email'):
            # only send if the user has already verified
            # at least one email address
            if user.emailaddress_set.filter(verified=True).exists():
                send_welcome_email.delay(user.pk, request.LANGUAGE_CODE)

    def on_email_confirmed(self, sender, request, email_address, **kwargs):
        """
        Signal handler to be called when a given email address was confirmed
        by a user.
        """
        if switch_is_active('welcome_email'):
            # only send if the user has exactly one verified (the given)
            # email address, in other words if it was just confirmed
            if not (email_address.user
                                 .emailaddress_set.exclude(pk=email_address.pk)
                                                  .exists()):
                send_welcome_email.delay(email_address.user.pk,
                                         request.LANGUAGE_CODE)

    def on_social_account_removed(self, sender, request, socialaccount, **kwargs):
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

    def on_ban_save(self, sender, instance, **kwargs):
        """
        Signal handler to be called when a given user ban is saved.
        """
        instance.user.is_active = not instance.is_active
        instance.user.save()

    def on_ban_delete(self, **kwargs):
        """
        Signal handler to be called when a user ban is deleted.
        """
        instance = kwargs.get('instance', None)
        if instance is not None:
            instance.user.is_active = True
            instance.user.save()
