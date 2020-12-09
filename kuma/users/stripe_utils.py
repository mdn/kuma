from datetime import datetime

import stripe
from django.conf import settings
from django.utils import timezone

from kuma.core.urlresolvers import reverse
from kuma.wiki.templatetags.jinja_helpers import absolutify

from . import signals
from .models import UserSubscription


def retrieve_stripe_subscription(customer):
    """
    Returns the first subscription it finds matching the configured stripe
    plan or, if there's none, just the first it finds.
    """
    first_subscription = None

    for subscription in customer.subscriptions.list().auto_paging_iter():
        if first_subscription is None:
            first_subscription = subscription

        # We have to use array indexing syntax, as stripe uses dicts to
        # represent its objects (dicts come with an .items method)
        for item in subscription["items"].auto_paging_iter():
            if item.plan.id == settings.STRIPE_PLAN_ID:
                # If we find a subscription matching the selected plan we
                # return that instead of whatever we found first
                return subscription

    return first_subscription


def retrieve_and_synchronize_subscription_info(user):
    """For the given user, if it has as 'stripe_customer_id' retrieve the info
    about the subscription if it's there. All packaged in a way that is
    practical for the stripe_subscription.html template.

    Also, whilst doing this check, we also verify that the UserSubscription record
    for this user is right. Doing that check is a second-layer check in case
    our webhooks have failed us.
    """
    subscription_info = None
    stripe_customer = get_stripe_customer(user)
    if stripe_customer:
        stripe_subscription_info = get_stripe_subscription_info(stripe_customer)
        if stripe_subscription_info:
            source = stripe_customer.default_source
            if source.object == "card":
                card = source
            elif source.object == "source":
                card = source.card
            else:
                raise ValueError(
                    f"unexpected stripe customer default_source of type {source.object!r}"
                )

            subscription_info = {
                "id": stripe_subscription_info.id,
                "amount": stripe_subscription_info.plan.amount,
                "brand": card.brand,
                "expires_at": f"{card.exp_month}/{card.exp_year}",
                "last4": card.last4,
                # Cards that are part of a "source" don't have a zip
                "zip": card.get("address_zip", None),
                "next_payment_at": datetime.fromtimestamp(
                    stripe_subscription_info.current_period_end
                ),
            }

            # To perfect the synchronization, take this opportunity to make sure
            # we have an up-to-date record of this.
            UserSubscription.set_active(user, stripe_subscription_info.id)
        else:
            # The user has a stripe_customer_id but no active subscription
            # on the current settings.STRIPE_PLAN_ID! Perhaps it has been canceled
            # and not updated in our own records.
            for user_subscription in UserSubscription.objects.filter(
                user=user, canceled__isnull=True
            ):
                user_subscription.canceled = timezone.now()
                user_subscription.save()

    return subscription_info


def create_stripe_customer_and_subscription_for_user(user, email, stripe_token):
    customer = (
        stripe.Customer.retrieve(user.stripe_customer_id)
        if user.stripe_customer_id
        else None
    )
    if not customer or customer.email != email:
        customer = stripe.Customer.create(email=email, source=stripe_token)
        user.stripe_customer_id = customer.id
        user.save()

    subscription = retrieve_stripe_subscription(customer)
    should_create_subscription = not subscription
    if should_create_subscription:
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"plan": settings.STRIPE_PLAN_ID}],
        )

    UserSubscription.set_active(user, subscription.id)

    if should_create_subscription:
        signals.subscription_created.send(None, user=user)


def cancel_stripe_customer_subscriptions(user):
    """Delete all subscriptions for a Stripe customer."""
    assert user.stripe_customer_id
    customer = stripe.Customer.retrieve(user.stripe_customer_id)
    canceled = []
    for sub in customer.subscriptions.data:
        s = stripe.Subscription.retrieve(sub.id)
        UserSubscription.set_canceled(user, s.id)
        s.delete()
        signals.subscription_cancelled.send(None, user=user)
        canceled.append(s)
    return canceled


def get_stripe_customer(user):
    if settings.STRIPE_PLAN_ID and user.stripe_customer_id:
        return stripe.Customer.retrieve(
            user.stripe_customer_id, expand=["default_source"]
        )


def get_stripe_subscription_info(stripe_customer):
    return retrieve_stripe_subscription(stripe_customer)


def create_missing_stripe_webhook():
    url_path = reverse("api.v1.stripe_hooks")
    url = (
        "https://" + settings.CUSTOM_WEBHOOK_HOSTNAME + url_path
        if settings.CUSTOM_WEBHOOK_HOSTNAME
        else absolutify(url_path)
    )

    # From https://stripe.com/docs/api/webhook_endpoints/create
    events = (
        # "Occurs whenever an invoice payment attempt succeeds."
        "invoice.payment_succeeded",
        # "Occurs whenever a customer’s subscription ends."
        # Also, if you go into the Stripe Dashboard, click Billing, Subscriptions,
        # and find a customer and click the "Cancel subscription" button, this
        # triggers.
        "customer.subscription.deleted",
    )

    for webhook in stripe.WebhookEndpoint.list().auto_paging_iter():
        if webhook.url == url and set(events) == set(webhook.enabled_events):
            return

    stripe.WebhookEndpoint.create(
        url=url,
        enabled_events=events,
    )
