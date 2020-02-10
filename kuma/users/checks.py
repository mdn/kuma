import stripe
from django.conf import settings
from django.core.checks import Error, register


@register()
def stripe_check(app_configs, **kwargs):
    if settings.STRIPE_SECRET_KEY == "testing" or (
        not settings.STRIPE_SECRET_KEY and not settings.STRIPE_PLAN_ID
    ):
        return []

    try:
        stripe.Plan.retrieve(settings.STRIPE_PLAN_ID)
    except stripe.error.StripeError as e:
        return [Error(f"invalid stripe config: {str(e)}")]

    return []
