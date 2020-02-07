import stripe
from django.conf import settings
from waffle import flag_is_active

from .constants import CONTRIBUTION_BETA_FLAG, RECURRING_PAYMENT_BETA_FLAG

stripe.api_key = settings.STRIPE_SECRET_KEY


def enabled(request):
    """Return True if contributions are enabled."""
    return bool(settings.MDN_CONTRIBUTION)


def popup_enabled(request):
    """Returns True if the popup is enabled for the user."""
    return (
        enabled(request)
        and hasattr(request, "user")
        and flag_is_active(request, CONTRIBUTION_BETA_FLAG)
    )


def recurring_payment_enabled(request):
    """Returns True if recurring payment is enabled for the user."""
    return popup_enabled(request) and flag_is_active(
        request, RECURRING_PAYMENT_BETA_FLAG
    )


def get_stripe_customer_data(stripe_customer_id):
    """Return select Stripe customer data as a simple dictionary."""
    stripe_data = {
        "stripe_plan_amount": 0,
        "stripe_card_last4": 0,
        "active_subscriptions": False,
    }
    customer = stripe.Customer.retrieve(stripe_customer_id)
    stripe_data["active_subscriptions"] = (
        True if customer["subscriptions"]["data"] else False
    )
    if customer["subscriptions"]["data"]:
        stripe_data["stripe_plan_amount"] = (
            customer["subscriptions"]["data"][0]["plan"]["amount"] / 100
        )
    if customer["sources"]["data"]:
        stripe_data["stripe_card_last4"] = customer["sources"]["data"][0]["card"][
            "last4"
        ]
    return stripe_data


def cancel_stripe_customer_subscription(stripe_customer_id):
    """Delete all subscriptions for a Stripe customer."""
    customer = stripe.Customer.retrieve(stripe_customer_id)
    for sub in customer["subscriptions"]["data"]:
        s = stripe.Subscription.retrieve(sub["id"])
        s.delete()
