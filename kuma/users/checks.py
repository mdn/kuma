import stripe
from django.conf import settings
from django.core.checks import Error, register


STRIPE_PLAN_ERROR = "kuma.users.E001"
STRIPE_PLAN_INACTIVE_ERROR = "kuma.users.E002"


@register()
def stripe_check(app_configs, **kwargs):
    errors = []

    if not (
        settings.STRIPE_SECRET_KEY
        or settings.STRIPE_PUBLIC_KEY
        or settings.STRIPE_PLAN_ID
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

    return errors
