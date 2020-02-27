import logging
from functools import wraps

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from stripe.error import StripeError
from waffle.decorators import waffle_flag

from kuma.core.decorators import ensure_wiki_domain, login_required

from .utils import (
    cancel_stripe_customer_subscription,
    get_stripe_customer_data,
)

log = logging.getLogger("kuma.payments.views")


@waffle_flag("subscription")
@ensure_wiki_domain
@never_cache
def contribute(request):
    return render(request, "payments/payments.html")


@waffle_flag("subscription")
@ensure_wiki_domain
@never_cache
def payment_terms(request):
    return render(request, "payments/terms.html")


@waffle_flag("subscription")
@ensure_wiki_domain
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
            cancel_stripe_customer_subscription(request.user.stripe_customer_id)
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
