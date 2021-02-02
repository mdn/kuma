from allauth.account.signals import email_confirmed, user_logged_in, user_signed_up
from allauth.socialaccount.signals import pre_social_login
from allauth.socialaccount.signals import social_account_removed
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from waffle import switch_is_active

from kuma.core.ga_tracking import (
    ACTION_AUTH_SUCCESSFUL,
    ACTION_FREE_NEWSLETTER,
    ACTION_PROFILE_CREATED,
    ACTION_RETURNING_USER_SIGNIN,
    CATEGORY_SIGNUP_FLOW,
    track_event,
)
from kuma.users.stripe_utils import cancel_stripe_customer_subscriptions

from .models import User, UserBan
from .tasks import send_welcome_email


@receiver(pre_social_login, dispatch_uid="users.pre_social_login")
def on_pre_social_login(sender, request, **kwargs):
    """
    Signal handler to be called when a given user has at least successfully
    authenticated with a provider but not necessarily fully logged in on
    our site. For example, if the user hasn't created a profile (e.g.
    agreeing to terms and conditions) the 'user_logged_in' won't fire until
    then.
    """
    sociallogin = kwargs.get("sociallogin")
    if sociallogin:
        track_event(
            CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, sociallogin.account.provider
        )


@receiver(user_signed_up, dispatch_uid="users.user_signed_up")
def on_user_signed_up(sender, request, user, **kwargs):
    """
    Signal handler to be called when a given user has signed up.
    """
    sociallogin = kwargs.get("sociallogin")
    if sociallogin:
        # If the user did the "social_auth_add" they already logged in and
        # all we needed to do was to "combine" their github social account
        # with their google social account. Or vice versa.
        if getattr(request, "social_auth_added", False):
            return

        track_event(
            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_CREATED, sociallogin.account.provider
        )

        # This puts a hint to the 'user_logged_in' signal, which'll happen
        # next, that the user needed to create a profile.
        request.signed_up = True

        track_event(
            CATEGORY_SIGNUP_FLOW,
            ACTION_FREE_NEWSLETTER,
            "opt-in" if user.is_newsletter_subscribed else "opt-out",
        )

    if switch_is_active("welcome_email"):
        # only send if the user has already verified
        # at least one email address
        if user.emailaddress_set.filter(verified=True).exists():
            transaction.on_commit(
                lambda: send_welcome_email.delay(user.pk, request.LANGUAGE_CODE)
            )


@receiver(user_logged_in, dispatch_uid="users.user_logged_in")
def on_user_logged_in(sender, request, user, **kwargs):
    # We've already recorded that they have signed up. No point sending one
    # about them logged in too.
    if getattr(request, "signed_up", False):
        return

    # They've already logged in through the effect of matching to an existing
    # profile.
    if getattr(request, "social_auth_added", False):
        return

    sociallogin = kwargs.get("sociallogin")
    if sociallogin:
        track_event(
            CATEGORY_SIGNUP_FLOW,
            ACTION_RETURNING_USER_SIGNIN,
            sociallogin.account.provider,
        )


@receiver(email_confirmed, dispatch_uid="users.email_confirmed")
def on_email_confirmed(sender, request, email_address, **kwargs):
    """
    Signal handler to be called when a given email address was confirmed
    by a user.
    """
    if switch_is_active("welcome_email"):
        # only send if the user has exactly one verified (the given)
        # email address, in other words if it was just confirmed
        user = email_address.user
        previous_emails = user.emailaddress_set.exclude(pk=email_address.pk)
        if not previous_emails.exists():
            transaction.on_commit(
                lambda: send_welcome_email.delay(user.pk, request.LANGUAGE_CODE)
            )


@receiver(social_account_removed, dispatch_uid="users.social_account_removed")
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
        request.session["sociallogin_provider"] = next_socialaccount.provider
        request.session.modified = True
    except (ObjectDoesNotExist, IndexError):
        pass


@receiver(post_save, sender=UserBan, dispatch_uid="users.user_ban.save")
def on_ban_save(sender, instance, **kwargs):
    """
    Signal handler to be called when a given user ban is saved.
    """
    user = instance.user
    user.is_active = not instance.is_active
    user.save()


@receiver(post_delete, sender=UserBan, dispatch_uid="users.user_ban.delete")
def on_ban_delete(sender, instance, **kwargs):
    """
    Signal handler to be called when a user ban is deleted.
    """
    user = instance.user
    user.is_active = True
    user.save()


@receiver(pre_delete, sender=User, dispatch_uid="users.unsubscribe_payments")
def unsubscribe_payments_on_user_delete(sender, instance, **kwargs):
    """Cancel Stripe subscriptions before deleting User."""
    user = instance
    if user.stripe_customer_id:
        # This may raise an exception if the Stripe API call fails.
        # This will stop User deletion while an admin investigates.
        cancel_stripe_customer_subscriptions(user)
