import json

import stripe
from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from raven.contrib.django.models import client as raven_client
from waffle import switch_is_active

from kuma.core.ga_tracking import (
    ACTION_SUBSCRIPTION_CANCELED,
    ACTION_SUBSCRIPTION_CREATED,
    CATEGORY_MONTHLY_PAYMENTS,
    track_event,
)
from kuma.users.models import User, UserSubscription
from kuma.users.stripe_utils import retrieve_stripe_prices


@require_GET
@never_cache
def subscription_config(request):
    if not switch_is_active("subscription"):
        return HttpResponseForbidden("subscription is not enabled")

    prices = []

    for price in retrieve_stripe_prices():
        prices.append(
            {
                "id": price.id,
                "currency": price.currency,
                "unit_amount": price.unit_amount,
            }
        )

    return JsonResponse(
        {"public_key": settings.STRIPE_PUBLIC_KEY, "prices": prices},
    )


@require_POST
@never_cache
def subscription_checkout(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("user not authenticated")
    elif not switch_is_active("subscription"):
        return HttpResponseForbidden("subscription is not enabled")

    data = request.POST

    if not user.stripe_customer_id:
        user.stripe_customer_id = stripe.Customer.create(email=user.email)["id"]
        user.save()

    callback_url = request.headers.get("Referer")
    checkout_session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        success_url=callback_url,
        cancel_url=callback_url,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[
            {
                "price": data.get("priceId"),
                "quantity": 1,
            }
        ],
    )
    return JsonResponse({"sessionId": checkout_session.id})


@require_POST
@never_cache
def subscription_customer_portal(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("user not authenticated")
    elif not switch_is_active("subscription"):
        return HttpResponseForbidden("subscription is not enabled")
    elif not user.stripe_customer_id:
        return HttpResponseForbidden("no existing stripe_customer_id")

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id, return_url=request.headers.get("Referer")
    )

    return JsonResponse({"url": session.url})


@csrf_exempt
@require_POST
@never_cache
def stripe_hooks(request):
    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("Invalid JSON payload")

    try:
        event = stripe.Event.construct_from(payload, stripe.api_key)
    except stripe.error.StripeError:
        raven_client.captureException()
        return HttpResponseBadRequest()

    # Generally, for this list of if-statements, see the create_missing_stripe_webhook
    # function.
    # The list of events there ought to at least minimally match what we're prepared
    # to deal with here.
    if event.type == "customer.subscription.created":
        obj = event.data.object
        for user in User.objects.filter(stripe_customer_id=obj.customer):
            UserSubscription.set_active(user, obj.id)
        track_event(CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_CREATED, "webhook")
    elif event.type == "customer.subscription.deleted":
        obj = event.data.object
        for user in User.objects.filter(stripe_customer_id=obj.customer):
            UserSubscription.set_canceled(user, obj.id)
        track_event(CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_CANCELED, "webhook")

    else:
        return HttpResponseBadRequest(
            f"We did not expect a Stripe webhook of type {event.type!r}"
        )

    return HttpResponse()
