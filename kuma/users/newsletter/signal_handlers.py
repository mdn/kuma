from allauth.account.signals import email_changed, user_signed_up
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from kuma.users.models import User
from kuma.users.signals import (
    newsletter_subscribed,
    newsletter_unsubscribed,
    subscription_cancelled,
    subscription_created,
    username_changed,
)

from .tasks import (
    create_or_update_contact,
    delete_contact,
)


@receiver(newsletter_subscribed, dispatch_uid="sendinblue.newsletter_subscribed")
def on_newsletter_subscribed(user, **kwargs):
    create_or_update_contact.delay(user.pk)


@receiver(newsletter_unsubscribed, dispatch_uid="sendinblue.newsletter_unsubscribed")
def on_newsletter_unsubscribed(user, **kwargs):
    delete_contact.delay(user.email)


@receiver(pre_delete, sender=User, dispatch_uid="sendinblue.user_pre_delete")
def on_user_delete(instance, **kwargs):
    if instance.is_newsletter_subscribed:
        delete_contact.delay(instance.email)


@receiver(user_signed_up, dispatch_uid="sendinblue.signed_up")
def on_signed_up(user, **kwargs):
    create_or_update_contact.delay(user.pk)


@receiver(username_changed, dispatch_uid="sendinblue.username_changed")
def on_username_changed(user, **kwargs):
    if user.is_newsletter_subscribed:
        create_or_update_contact.delay(user.pk)


@receiver(email_changed, dispatch_uid="sendinblue.email_changed")
def on_email_changed(user, from_email_address, to_email_address, **kwargs):
    if user.is_newsletter_subscribed:
        delete_contact.delay(from_email_address.email)
        create_or_update_contact.delay(user.pk)


@receiver(subscription_created, dispatch_uid="sendinblue.subscription_created")
def on_subscription_created(user, **kwargs):
    create_or_update_contact.delay(user.pk)


@receiver(subscription_cancelled, dispatch_uid="sendinblue.subscription_cancelled")
def on_subscription_cancelled(user, **kwargs):
    create_or_update_contact.delay(user.pk)
