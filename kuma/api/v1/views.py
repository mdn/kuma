import json

import stripe
from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from raven.contrib.django.models import client as raven_client
from rest_framework import status
from rest_framework.response import Response
from waffle import flag_is_active
from waffle.decorators import waffle_flag

from kuma.api.v1.forms import AccountSettingsForm
from kuma.core.ga_tracking import (
    ACTION_SUBSCRIPTION_CANCELED,
    ACTION_SUBSCRIPTION_CREATED,
    ACTION_SUBSCRIPTION_FEEDBACK,
    CATEGORY_MONTHLY_PAYMENTS,
    track_event,
)
from kuma.users.models import User, UserSubscription
from kuma.users.stripe_utils import retrieve_and_synchronize_stripe_subscription
from kuma.users.templatetags.jinja_helpers import get_avatar_url


@never_cache
@require_GET
def whoami(request):
    """
    Return a JSON object representing the current user, either
    authenticated or anonymous.
    """
    user = request.user
    if user.is_authenticated:
        data = {
            "username": user.username,
            "is_authenticated": True,
            "avatar_url": get_avatar_url(user),
            "email": user.email,
            "subscriber_number": user.subscriber_number,
        }
        if UserSubscription.objects.filter(user=user, canceled__isnull=True).exists():
            data["is_subscriber"] = True
        if user.is_staff:
            data["is_staff"] = True
        if user.is_superuser:
            data["is_superuser"] = True
        if user.is_beta_tester:
            data["is_beta_tester"] = True
    else:
        data = {}

    geo = {}
    # https://aws.amazon.com/about-aws/whats-new/2020/07/cloudfront-geolocation-headers/
    cloudfront_country_header = "HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME"
    cloudfront_country_value = request.META.get(cloudfront_country_header)
    if cloudfront_country_value:
        geo["country"] = cloudfront_country_value
    if geo:
        data["geo"] = geo

    return JsonResponse(data)


@never_cache
def account_settings(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("not signed in")
    if request.method == "DELETE":
        # This should cease to be necessary once we get rid of the Wiki models.
        anon, _ = User.objects.get_or_create(username="Anonymous")
        user.documentdeletionlog_set.update(user=anon)
        user.created_revisions.update(creator=anon)
        user.created_attachment_revisions.update(creator=anon)
        user.bans.update(user=anon)
        user.bans_issued.update(by=anon)

        user.delete()
        return JsonResponse({"deleted": True})
    elif request.method == "POST":
        form = AccountSettingsForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

        set_locale = None
        if form.cleaned_data.get("locale"):
            user.locale = set_locale = form.cleaned_data["locale"]
            user.save()

        response = JsonResponse({"ok": True})
        if set_locale:
            response.set_cookie(
                key=settings.LANGUAGE_COOKIE_NAME,
                value=set_locale,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
            )

        return response

    context = {
        "csrfmiddlewaretoken": get_token(request),
        "locale": user.locale,
        "subscription": retrieve_and_synchronize_stripe_subscription(user),
    }
    return JsonResponse(context)


@waffle_flag("subscription")
@never_cache
@require_POST
def send_subscriptions_feedback(request):
    """
    Sends feedback to Google Analytics. This is done on the
    backend to ensure that all feedback is collected, even
    from users with DNT or where GA is disabled.
    """
    data = json.loads(request.body)
    feedback = (data.get("feedback") or "").strip()

    if not feedback:
        return HttpResponseBadRequest("no feedback")

    track_event(
        CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_FEEDBACK, data["feedback"]
    )
    return HttpResponse(status=204)


@require_POST
@never_cache
def subscription_checkout(request):
    user = request.user
    if not user.is_authenticated or not flag_is_active(request, "subscription"):
        return Response(None, status=status.HTTP_403_FORBIDDEN)

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
    return JsonResponse({"sessionId": checkout_session.id}, status=status.HTTP_200_OK)


@require_POST
@never_cache
def subscription_customer_portal(request):
    user = request.user
    if not user.is_authenticated or not flag_is_active(request, "subscription"):
        return Response(None, status=status.HTTP_403_FORBIDDEN)

    assert user.stripe_customer_id

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id, return_url=request.headers.get("Referer")
    )

    return JsonResponse({"url": session.url}, status=status.HTTP_200_OK)


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
