import stripe
from django.conf import settings
from django.core.checks import Error

from .stripe_utils import create_missing_stripe_webhook, retrieve_stripe_prices

STRIPE_ERROR = "kuma.users.E001"
STRIPE_PRICES_MISSING_ERROR = "kuma.users.E002"
STRIPE_PRICE_INACTIVE_ERROR = "kuma.users.E003"
STRIPE_PRICE_ERROR = "kuma.users.E004"


def stripe_check(app_configs, **kwargs):
    errors = []

    if not settings.STRIPE_SECRET_KEY:
        return errors

    try:
        prices = retrieve_stripe_prices()
        if not prices:
            errors.append(
                Error(
                    "STRIPE_PRICE_IDS is empty",
                    id=STRIPE_PRICES_MISSING_ERROR,
                )
            )

        for price in prices:
            if not price.active:
                errors.append(
                    Error(
                        f"{price.id} points to an inactive Stripe price",
                        id=STRIPE_PRICE_INACTIVE_ERROR,
                    )
                )
    except stripe.error.StripeError as error:
        errors.append(
            Error(f"unable to retrieve Stripe plan: {error}", id=STRIPE_PRICE_ERROR)
        )

    try:
        create_missing_stripe_webhook()
    except stripe.error.StripeError as error:
        errors.append(
            Error(f"unable get or create Stripe webhooks: {error}", id=STRIPE_ERROR)
        )

    return errors
