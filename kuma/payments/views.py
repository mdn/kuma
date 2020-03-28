import logging
import json

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse

from stripe.error import StripeError
from waffle.decorators import waffle_flag

from kuma.core.decorators import ensure_wiki_domain, login_required
from kuma.core.ga_tracking import (
    CATEGORY_MONTHLY_PAYMENTS,
    ACTION_FEEDBACK,
    track_event,
)
from kuma.users.models import UserSubscription

from .utils import (
    cancel_stripe_customer_subscription,
    get_stripe_customer_data,
)

log = logging.getLogger("kuma.payments.views")


@never_cache
def index(request):
    return render(request, "payments/index.html")


@waffle_flag("subscription")
@never_cache
def thank_you(request):
    return render(request, "payments/thank-you.html")


@waffle_flag("subscription")
@never_cache
@require_POST
def send_feedback(request):
    """
    Sends feedback to Google Analytics. This is done on the
    backend to ensure that all feedback is collected, even
    from users with DNT or where GA is disabled.
    """
    data = json.loads(request.body)
    track_event(CATEGORY_MONTHLY_PAYMENTS, ACTION_FEEDBACK, data["feedback"])
    return HttpResponse(status=204)


@waffle_flag("subscription")
@never_cache
def payment_terms(request):
    return render(request, "payments/terms.html")


@ensure_wiki_domain
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
            for subscription_id in cancel_stripe_customer_subscription(
                request.user.stripe_customer_id
            ):
                UserSubscription.set_canceled(request.user, subscription_id)
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
