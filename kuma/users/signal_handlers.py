from datetime import timedelta

from allauth.account.signals import (
    email_confirmed,
    user_logged_in,
    user_signed_up)
from allauth.socialaccount.signals import social_account_removed
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from waffle import switch_is_active

from kuma.payments.utils import cancel_stripe_customer_subscription
from kuma.wiki.jobs import DocumentContributorsJob
from kuma.core.ga_tracking import (
    ACTION_SIGN_IN,
    ACTION_SIGN_UP,
    CATEGORY_SIGNUP_FLOW,
    track_event)

from .models import User, UserBan
from .tasks import send_welcome_email


@receiver(user_signed_up, dispatch_uid='users.user_signed_up')
def on_user_signed_up(sender, request, user, **kwargs):
    """
    Signal handler to be called when a given user has signed up.
    """
    if switch_is_active('welcome_email'):
        # only send if the user has already verified
        # at least one email address
        if user.emailaddress_set.filter(verified=True).exists():
            transaction.on_commit(
                lambda: send_welcome_email.delay(user.pk, request.LANGUAGE_CODE)
            )


@receiver(user_logged_in, dispatch_uid='users.user_logged_in')
def on_user_logged_in(sender, request, user, **kwargs):
    sociallogin = kwargs.get('sociallogin')
    print("SOCIALLOGIN", repr(sociallogin))
    # assert False
    if sociallogin:
        # Thing is, if someone signs in for the very first time, it'll
        # trigger two signals: 'user_signed_up' *and* 'user_logged_in'.
        # If that happens, we only want to send *1* tracking event.
        # If we listen to both signals we'd get potentially send one
        # tracking event too many. So, use the `SocialAccount.last_login`
        # and `SocialAccount.date_joined` to figure out if this was the
        # the first time.
        #
        # Due to how the Django ORM assigns dates, it could be that the
        # two dates are only different in the number of
        if is_almost_same_dates(
            sociallogin.account.last_login,
            sociallogin.account.date_joined
        ):
            # It's a sign UP!
            track_event(
                CATEGORY_SIGNUP_FLOW,
                ACTION_SIGN_UP,
                sociallogin.account.provider)
        else:
            track_event(
                CATEGORY_SIGNUP_FLOW,
                ACTION_SIGN_IN,
                sociallogin.account.provider)


def is_almost_same_dates(date1, date2, epislon=timedelta(minutes=1)):
    """Return true if both dates are truthy and sufficiently close"""
    return (
        date1 and date2 and
        abs(date1 - date2) < epislon)


@receiver(email_confirmed, dispatch_uid='users.email_confirmed')
def on_email_confirmed(sender, request, email_address, **kwargs):
    """
    Signal handler to be called when a given email address was confirmed
    by a user.
    """
    if switch_is_active('welcome_email'):
        # only send if the user has exactly one verified (the given)
        # email address, in other words if it was just confirmed
        user = email_address.user
        previous_emails = user.emailaddress_set.exclude(pk=email_address.pk)
        if not previous_emails.exists():
            transaction.on_commit(
                lambda: send_welcome_email.delay(user.pk, request.LANGUAGE_CODE)
            )


@receiver(social_account_removed, dispatch_uid='users.social_account_removed')
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


@receiver(post_save, sender=UserBan, dispatch_uid='users.user_ban.save')
def on_ban_save(sender, instance, **kwargs):
    """
    Signal handler to be called when a given user ban is saved.
    """
    user = instance.user
    user.is_active = not instance.is_active
    user.save()
    invalidate_document_contribution(user)


@receiver(post_delete, sender=UserBan, dispatch_uid='users.user_ban.delete')
def on_ban_delete(sender, instance, **kwargs):
    """
    Signal handler to be called when a user ban is deleted.
    """
    user = instance.user
    user.is_active = True
    user.save()
    invalidate_document_contribution(user)


def invalidate_document_contribution(user):
    """
    Invalidate the contributor list for Documents the user has edited.

    This will remove them if they have been banned, and add them if they
    have been unbanned.
    """
    revisions = user.created_revisions
    doc_ids = set(revisions.values_list('document_id', flat=True))
    job = DocumentContributorsJob()
    for doc_id in doc_ids:
        job.invalidate(doc_id)


@receiver(pre_delete, sender=User, dispatch_uid='users.unsubscribe_payments')
def unsubscribe_payments_on_user_delete(sender, instance, **kwargs):
    """Cancel Stripe subscriptions before deleting User."""
    user = instance
    if user.stripe_customer_id:
        # This may raise an exception if the Stripe API call fails.
        # This will stop User deletion while an admin investigates.
        cancel_stripe_customer_subscription(user.stripe_customer_id)
