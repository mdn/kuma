import stripe
from django.conf import settings
from django.core.checks import Error

from .stripe_utils import create_missing_stripe_webhook

STRIPE_ERROR = "kuma.users.E001"


def stripe_check(app_configs, **kwargs):
    errors = []

    if not settings.STRIPE_SECRET_KEY:
        return errors

    try:
        create_missing_stripe_webhook()
    except stripe.error.StripeError as error:
        errors.append(
            Error(
                f"unable get or create Stripe webhooks: {error}", id=STRIPE_ERROR
            )
        )

    return errors
