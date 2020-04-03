import stripe
from django.conf import settings

from kuma.core.urlresolvers import reverse
from kuma.wiki.templatetags.jinja_helpers import absolutify

from .models import UserSubscription


def retrieve_stripe_subscription(customer):
    for subscription in customer.subscriptions.list().auto_paging_iter():
        # We have to use array indexing syntax, as stripe uses dicts to
        # represent its objects (dicts come with an .items method)
        for item in subscription["items"].auto_paging_iter():
            if item.plan.id == settings.STRIPE_PLAN_ID:
                return subscription

    return None


def create_stripe_customer_and_subscription_for_user(user, email, stripe_token):
    customer = (
        stripe.Customer.retrieve(user.stripe_customer_id)
        if user.stripe_customer_id
        else None
    )
    if not customer or customer.email != email:
        customer = stripe.Customer.create(email=email, source=stripe_token,)
        user.stripe_customer_id = customer.id
        user.save()

    subscription = retrieve_stripe_subscription(customer)
    if not subscription:
        subscription = stripe.Subscription.create(
            customer=customer.id, items=[{"plan": settings.STRIPE_PLAN_ID}],
        )

    UserSubscription.set_active(user, subscription.id)


def get_stripe_customer(user):
    if settings.STRIPE_PLAN_ID and user.stripe_customer_id:
        return stripe.Customer.retrieve(
            user.stripe_customer_id, expand=["default_source"]
        )


def get_stripe_subscription_info(stripe_customer):
    return retrieve_stripe_subscription(stripe_customer)


def create_missing_stripe_webhook():
    url_path = reverse("users.stripe_hooks")
    url = (
        "https://" + settings.STRIPE_WEBHOOK_HOSTNAME + url_path
        if settings.STRIPE_WEBHOOK_HOSTNAME
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
        url=url, enabled_events=events,
    )
