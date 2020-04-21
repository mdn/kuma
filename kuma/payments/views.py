import logging
import datetime

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from stripe.error import StripeError
from waffle.decorators import waffle_flag

from kuma.core.decorators import ensure_wiki_domain, login_required
from kuma.users.models import User
from kuma.users.stripe_utils import cancel_stripe_customer_subscriptions

from .utils import get_stripe_customer_data

log = logging.getLogger("kuma.payments.views")


@never_cache
def index(request):
    highest_subscriber_number = User.get_highest_subscriber_number()
    # TODO: This is never unit tested because our tests never test SSR rendering.
    # See https://github.com/mdn/kuma/issues/6797
    context = {"next_subscriber_number": highest_subscriber_number + 1}
    return render(request, "payments/index.html", context)


@waffle_flag("subscription")
@never_cache
def thank_you(request):
    return render(request, "payments/thank-you.html")


@waffle_flag("subscription")
@never_cache
def payment_terms(request):
    return render(request, "payments/terms.html")


@waffle_flag("subscription")
@login_required
@never_cache
def recurring_payment_management(request):
    context = {
        "support_mail_link": "mailto:"
        + settings.CONTRIBUTION_SUPPORT_EMAIL
        + "?Subject=Recurring%20payment%20support",
        "support_mail": settings.CONTRIBUTION_SUPPORT_EMAIL,
        "cancel_request": False,
        "cancel_success": False,
    }

    if request.user.stripe_customer_id and "stripe_cancel_subscription" in request.POST:
        context["cancel_request"] = True
        cancel_success = False
        try:
            cancel_stripe_customer_subscriptions(request.user)
        except StripeError:
            log.exception(
                "Stripe subscription cancellation: Stripe error for %s [%s]",
                request.user.username,
                request.user.email,
            )
        else:
            cancel_success = True
        context["cancel_success"] = cancel_success

    if request.user.stripe_customer_id:
        data = {"active_subscriptions": False}
        try:
            data = get_stripe_customer_data(request.user.stripe_customer_id)
        except StripeError:
            log.exception(
                "Stripe subscription data: Stripe error for %s [%s]",
                request.user.username,
                request.user.email,
            )
        context.update(data)
    return render(request, "payments/management.html", context)
