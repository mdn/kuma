import stripe
from django.conf import settings
from django.core.checks import Error

from .stripe_utils import create_missing_stripe_webhook

STRIPE_PLAN_ERROR = "kuma.users.E001"
STRIPE_PLAN_INACTIVE_ERROR = "kuma.users.E002"


def stripe_check(app_configs, **kwargs):
    errors = []

    # Unfortunately system checks get run with testing settings in our CI,
    # so we need to check for the testing setting value
    # Related issue: https://github.com/mdn/kuma/issues/6481
    if settings.STRIPE_SECRET_KEY == "testing" or (
        not settings.STRIPE_SECRET_KEY
        and not settings.STRIPE_PUBLIC_KEY
        and not settings.STRIPE_PLAN_ID
    ):
        return errors

    try:
        plan = stripe.Plan.retrieve(settings.STRIPE_PLAN_ID)
        if not plan.active:
            errors.append(
                Error(
                    f"{settings.STRIPE_PLAN_ID} points to an inactive Strip plan",
                    id=STRIPE_PLAN_INACTIVE_ERROR,
                )
            )
    except stripe.error.StripeError as error:
        errors.append(
            Error(f"unable to retrieve stripe plan: {error}", id=STRIPE_PLAN_ERROR)
        )

    try:
        create_missing_stripe_webhook()
    except stripe.error.StripeError as error:
        errors.append(
            Error(f"unable get or create strip webhooks: {error}", id=STRIPE_PLAN_ERROR)
        )

    return errors
