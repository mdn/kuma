import stripe
from django.conf import settings
from django.utils import timezone

from kuma.core.urlresolvers import reverse
from kuma.wiki.templatetags.jinja_helpers import absolutify

from .models import UserSubscription


def retrieve_stripe_prices():
    return [stripe.Price.retrieve(id) for id in settings.STRIPE_PRICE_IDS]


def retrieve_and_synchronize_stripe_subscription(user):
    assert user.stripe_customer_id

    subscriptions = stripe.Subscription.list(
        customer=user.stripe_customer_id, status="active", limit=1
    )

    if subscriptions.data:
        subscription = subscriptions.data[0]
        UserSubscription.set_active(user, subscription.id)
        return subscription

    for user_subscription in UserSubscription.objects.filter(
        user=user, canceled__isnull=True
    ):
        user_subscription.canceled = timezone.now()
        user_subscription.save()

    return None


def cancel_stripe_customer_subscriptions(user):
    """Delete all subscriptions for a Stripe customer."""
    assert user.stripe_customer_id
    canceled = []
    for subscription in stripe.Subscription.list(
        customer=user.stripe_customer_id
    ).auto_paging_iter():
        UserSubscription.set_canceled(user, subscription.id)
        subscription.delete()
        canceled.append(subscription)
    return canceled


def create_missing_stripe_webhook():
    url_path = reverse("api.v1.stripe_hooks")
    url = absolutify(url_path)

    # From https://stripe.com/docs/api/webhook_endpoints/create
    events = ("customer.subscription.created", "customer.subscription.deleted")

    for webhook in stripe.WebhookEndpoint.list().auto_paging_iter():
        if webhook.url == url and set(events) == set(webhook.enabled_events):
            return

    stripe.WebhookEndpoint.create(
        url=url,
        enabled_events=events,
    )
