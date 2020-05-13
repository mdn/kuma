from allauth.account.signals import email_changed, user_signed_up
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from kuma.users.models import User, UserSubscription
from kuma.users.signals import (
    newsletter_subscribed,
    newsletter_unsubscribed,
    subscription_cancelled,
    subscription_created,
)

from .tasks import (
    sendinblue_create_or_update_contact,
    sendinblue_delete_contact,
)


@receiver(newsletter_subscribed, dispatch_uid="sendinblue.newsletter_subscribed")
def on_newsletter_subscribed(user, **kwargs):
    sendinblue_create_or_update_contact.delay(user.email)


@receiver(newsletter_unsubscribed, dispatch_uid="sendinblue.newsletter_unsubscribed")
def on_newsletter_unsubscribed(user, **kwargs):
    sendinblue_delete_contact.delay(user.email)


@receiver(pre_delete, sender=User, dispatch_uid="sendinblue.user_pre_delete")
def on_user_delete(instance, **kwargs):
    if instance.is_newsletter_subscribed:
        sendinblue_delete_contact.delay(instance.email)


def newsletter_receiver(*receiver_args, **receiver_kwargs):
    """
    Decorator wrapping the signal handler @receiver decorator. It needs to be called
    with a signal that gets user as an argument. It then only calls the decorated
    function if the given user is subscribed to the newsletter.
    """

    def receive_decorator(func):
        def newsletter_check_decorator(user, *signal_args, **signal_kwargs):
            if user.is_newsletter_subscribed:
                func(user, *signal_args, **signal_kwargs)

        return receiver(*receiver_args, **receiver_kwargs)(newsletter_check_decorator)

    return receive_decorator


@newsletter_receiver(user_signed_up, dispatch_uid="sendinblue.signed_up")
def on_signed_up(user, **kwargs):
    sendinblue_create_or_update_contact.delay(user.email, {"IS_PAYING": False})


@newsletter_receiver(email_changed, dispatch_uid="sendinblue.email_changed")
def on_email_changed(user, from_email_address, to_email_address, **kwargs):
    sendinblue_delete_contact.delay(from_email_address.email)
    sendinblue_create_or_update_contact.delay(
        to_email_address.email,
        {
            "IS_PAYING": UserSubscription.objects.filter(
                user=user, canceled__isnull=True
            ).exists()
        },
    )


@newsletter_receiver(
    subscription_created, dispatch_uid="sendinblue.subscription_created"
)
def on_subscription_created(user, **kwargs):
    sendinblue_create_or_update_contact.delay(user.email, {"IS_PAYING": True})


@newsletter_receiver(
    subscription_cancelled, dispatch_uid="sendinblue.subscription_cancelled"
)
def on_subscription_cancelled(user, **kwargs):
    sendinblue_create_or_update_contact.delay(user.email, {"IS_PAYING": False})
