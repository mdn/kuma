import json
import os
from datetime import datetime
from urllib.parse import urlparse

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from ratelimit.decorators import ratelimit
from raven.contrib.django.models import client as raven_client
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from waffle import flag_is_active
from waffle.decorators import waffle_flag
from waffle.models import Flag, Sample, Switch

from kuma.api.v1.serializers import BCSignalSerializer
from kuma.core.email_utils import render_email
from kuma.core.ga_tracking import (
    ACTION_SUBSCRIPTION_CANCELED,
    ACTION_SUBSCRIPTION_CREATED,
    ACTION_SUBSCRIPTION_FEEDBACK,
    CATEGORY_MONTHLY_PAYMENTS,
    track_event,
)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import requests_retry_session, send_mail_retrying
from kuma.search.filters import (
    HighlightFilterBackend,
    KeywordQueryBackend,
    LanguageFilterBackend,
    SearchQueryBackend,
    TagGroupFilterBackend,
)
from kuma.search.search import SearchView
from kuma.users.models import User, UserSubscription
from kuma.users.newsletter.utils import refresh_is_user_newsletter_subscribed
from kuma.users.stripe_utils import (
    cancel_stripe_customer_subscriptions,
    create_stripe_customer_and_subscription_for_user,
    retrieve_and_synchronize_subscription_info,
)
from kuma.users.templatetags.jinja_helpers import get_avatar_url
from kuma.wiki.templatetags.jinja_helpers import absolutify


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

        # This is rather temporary field. Once we're off the Wiki and into Yari
        # this no longer makes sense to keep.
        data["wiki_contributions"] = user.created_revisions.count()
    else:
        data = {}

    # Add waffle data to the dict we're going to be returning.
    # This is what the waffle.wafflejs() template tag does, but we're
    # doing it via an API instead of hardcoding the settings into
    # the HTML page. See also from waffle.views._generate_waffle_js.
    #
    # Note that if we upgrade django-waffle, version 15 introduces a
    # pluggable flag model, and the approved way to get all flag
    # objects will then become:
    #    get_waffle_flag_model().get_all()
    #
    data["waffle"] = {
        "flags": {f.name: True for f in Flag.get_all() if f.is_active(request)},
        "switches": {s.name: True for s in Switch.get_all() if s.is_active()},
        "samples": {s.name: True for s in Sample.get_all() if s.is_active()},
    }
    return JsonResponse(data)


class APIDocumentSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True, max_length=255)
    slug = serializers.CharField(read_only=True, max_length=255)
    locale = serializers.CharField(read_only=True, max_length=7)
    excerpt = serializers.ReadOnlyField(source="get_excerpt")


class APILanguageFilterBackend(LanguageFilterBackend):
    """Override of kuma.search.filters:LanguageFilterBackend that is almost
    exactly the same except the locale comes from custom code rather than
    via kuma.core.i18n.get_language_from_request because that can't be used
    in the API.

    Basically, it's the same exact functionality but ...
    """

    def filter_queryset(self, request, queryset, view):
        locale = request.GET.get("locale") or settings.LANGUAGE_CODE
        if locale not in settings.ACCEPTED_LOCALES:
            raise serializers.ValidationError({"error": "Not a valid locale code"})
        request.LANGUAGE_CODE = locale
        return super(APILanguageFilterBackend, self).filter_queryset(
            request, queryset, view
        )


class APISearchView(SearchView):
    serializer_class = APIDocumentSerializer
    renderer_classes = [JSONRenderer]
    filter_backends = (
        SearchQueryBackend,
        KeywordQueryBackend,
        TagGroupFilterBackend,
        APILanguageFilterBackend,
        HighlightFilterBackend,
    )


search = never_cache(APISearchView.as_view())


@ratelimit(key="user_or_ip", rate="10/d", block=True)
@api_view(["POST"])
def bc_signal(request):
    if not settings.ENABLE_BCD_SIGNAL:
        return Response("not enabled", status=status.HTTP_400_BAD_REQUEST)

    serializer = BCSignalSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(["POST", "GET", "DELETE"])
@never_cache
def subscriptions(request):
    if not request.user.is_authenticated or not flag_is_active(request, "subscription"):
        return Response(None, status=status.HTTP_403_FORBIDDEN)

    if request.method == "POST":
        create_stripe_customer_and_subscription_for_user(
            request.user, request.user.email, request.data["stripe_token"]
        )
        return Response(None, status=status.HTTP_201_CREATED)
    elif request.method == "DELETE":
        cancelled = cancel_stripe_customer_subscriptions(request.user)
        if cancelled:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response("nothing to cancel", status=status.HTTP_410_GONE)

    all_subscriptions = []
    subscription_info = retrieve_and_synchronize_subscription_info(request.user)
    if subscription_info:
        all_subscriptions.append(subscription_info)

    return Response({"subscriptions": all_subscriptions})


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

    if event.type == "invoice.payment_succeeded":
        invoice = event.data.object
        _send_payment_received_email(invoice, request.LANGUAGE_CODE)
        track_event(
            CATEGORY_MONTHLY_PAYMENTS,
            ACTION_SUBSCRIPTION_CREATED,
            f"{settings.CONTRIBUTION_AMOUNT_USD:.2f}",
        )

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


def _send_payment_received_email(invoice, locale):
    user = get_user_model().objects.get(stripe_customer_id=invoice.customer)
    subscription_info = retrieve_and_synchronize_subscription_info(user)
    locale = locale or settings.WIKI_DEFAULT_LANGUAGE
    context = {
        "payment_date": datetime.fromtimestamp(invoice.created),
        "next_payment_date": subscription_info["next_payment_at"],
        "invoice_number": invoice.number,
        "cost": invoice.total / 100,
        "credit_card_brand": subscription_info["brand"],
        "manage_subscription_url": absolutify(reverse("payment_management")),
        "faq_url": absolutify(reverse("payments_index")),
        "contact_email": settings.CONTRIBUTION_SUPPORT_EMAIL,
    }
    with translation.override(locale):
        subject = render_email("users/email/payment_received/subject.ltxt", context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        plain = render_email("users/email/payment_received/plain.ltxt", context)

        send_mail_retrying(
            subject,
            plain,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            attachment={
                "name": os.path.basename(urlparse(invoice.invoice_pdf).path),
                "bytes": _download_from_url(invoice.invoice_pdf),
                "mime": "application/pdf",
            },
        )


def _download_from_url(url):
    pdf_download = requests_retry_session().get(url)
    pdf_download.raise_for_status()
    return pdf_download.content


@csrf_exempt
@require_POST
@never_cache
def sendinblue_hooks(request):
    # Sendinblue does not sign its webhook requests, hence the event handlers following
    # are different from the Stripe ones, in that they treat the event as a notification
    # of a _potential_ change, while still needing to contact sendinblue to verify that
    # it actually happened.
    try:
        payload = json.loads(request.body)
        event = payload["event"]
        email = payload["email"]
    except (json.decoder.JSONDecodeError, KeyError) as exception:
        return HttpResponseBadRequest(
            f"{exception.__class__.__name__} on {request.body}"
        )

    if event == "unsubscribe":
        refresh_is_user_newsletter_subscribed(email)
        return HttpResponse()
    else:
        return HttpResponseBadRequest(
            f"We did not expect a Sendinblue webhook of type {event['event']!r}"
        )
