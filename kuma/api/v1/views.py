import json
import os
from datetime import datetime
from urllib.parse import urlparse

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, query, Search
from ratelimit.decorators import ratelimit
from raven.contrib.django.models import client as raven_client
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from waffle import flag_is_active
from waffle.decorators import waffle_flag
from waffle.models import Flag, Sample, Switch

from kuma.api.v1.serializers import BCSignalSerializer, UserDetailsSerializer
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
from kuma.users.models import User, UserSubscription
from kuma.users.newsletter.utils import refresh_is_user_newsletter_subscribed
from kuma.users.signals import (
    newsletter_subscribed,
    newsletter_unsubscribed,
    username_changed,
)
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


def search(request, locale=None):
    # Validate the input...
    # XXX Switch to using forms
    if locale:
        locales = [locale]
    else:
        locales = request.GET.getlist("locales") or []
    params = {
        "locales": [x.lower() for x in locales],
        "include_archive": False,
        "query": request.GET.get("q"),
        "size": 10,
        "page": 1,
        "sort": "relevance",  # 'best' or 'popularity'
    }
    assert params["query"]  # XXX

    results = _find(params)

    return JsonResponse(results)


def _find(params, total_only=False, make_suggestions=False, min_suggestion_score=0.8):

    # Perform the search
    client = Elasticsearch(settings.ES_URLS)
    s = Search(
        using=client,
        index="yari_doc",  # XXX settings?
    )
    if make_suggestions:
        # XXX research if it it's better to use phrase suggesters and if
        # that works
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters.html#phrase-suggester
        s = s.suggest("title_suggestions", params["query"], term={"field": "title"})
        s = s.suggest("body_suggestions", params["query"], term={"field": "body"})

    if params["locales"]:
        s = s.filter("terms", locale=params["locales"])
    if not params["include_archive"]:
        s = s.filter("term", archived=False)

    # XXX
    # The problem with multi_match is that it's not a phrase search
    # so searching for "javascript yibberish" will basically be the
    # same as searching for "javascript". And if you ask for suggestions
    # it'll probably come back with a (term) suggestion of
    # "javascript jibberish" which, yes, is different but still will just
    # result in what you would have gotten if you searched for "javascript".
    # The research to do is to see if it's better do use a boosted (OR) boolean
    # search with `match_phrase` and make that the primary strategy. Then,
    # only if nothing can be found, fall back to `multi_match`.
    # This choice of strategy should probably inform the use of suggestions too.
    q = Q("multi_match", query=params["query"], fields=["title^10", "body"])

    s = s.highlight_options(
        pre_tags=["<mark>"],
        post_tags=["</mark>"],
        number_of_fragments=3,
        fragment_size=120,
        encoder="html",
    )
    s = s.highlight("title", "body")

    if params["sort"] == "relevance":
        s = s.sort("_score", "-popularity")
        s = s.query(q)
    elif params["popularity"]:
        s = s.sort("-popularity", "_score")
        s = s.query(q)
    else:
        popularity_factor = 1
        boost_mode = 1
        s = s.query(
            "function_score",
            matcher=q,
            functions=[
                query.SF(
                    "field_value_factor",
                    field="popularity",
                    factor=popularity_factor,
                    missing=0.0,
                )
            ],
            boost_mode=boost_mode,
        )

    s = s.source(excludes=["body"])

    s = s[params["size"] * (params["page"] - 1) : params["size"] * params["page"]]

    # XXX make this retry with `redo`. Just got to learn from our mistakes first
    # in really understanding what kinds of errors we're going to get!
    response = s.execute()
    if total_only:
        return response.hits.total

    metadata = {
        "took_ms": response.took,
        "total": response.hits.total,
        "size": params["size"],
        "page": params["page"],
    }
    documents = []
    for hit in response:
        try:
            body_highlight = list(hit.meta.highlight.body)
        except AttributeError:
            body_highlight = []
        try:
            title_highlight = list(hit.meta.highlight.title)
        except AttributeError:
            title_highlight = []

        d = {
            "mdn_url": hit.meta.id,
            "score": hit.meta.score,
            "title": hit.title,
            "locale": hit.locale,
            "slug": hit.slug,
            "popularity": hit.popularity,
            "archived": hit.archived,
            "highlight": {
                "body": body_highlight,
                "title": title_highlight,
            },
        }
        documents.append(d)

    try:
        suggest = getattr(response, "suggest")
    except AttributeError:
        suggest = None

    suggestions = []
    if suggest:
        suggestion_strings = _unpack_suggestions(
            params["query"],
            response.suggest,
            ("body_suggestions", "title_suggestions"),
        )

        for score, string in suggestion_strings:
            if score > min_suggestion_score or 1:
                # Sure, this is different way to spell, but what will it yield
                # if you actually search it?
                # XXX Oftentimes, when searching for phrases, like "WORD GOOBLYGOK"
                # Elasticsearch has already decided to ignore the "GOOBLYGOK" part,
                # and what you have so far is the 123 search results that exists
                # thanks to the "WORD" part. So if you re-attempt a search
                # for "WORD GOOBLYGOOK" (extra "O"), you'll still get the same
                # exact 123 search results.
                total = _find(params, total_only=True)
                if total["value"] > 0:
                    suggestions.append(
                        {
                            "text": string,
                            "total": total,
                        }
                    )
                    # Since they're sorted by score, it's usually never useful
                    # to suggestion more than exactly 1 good suggestion.
                    break

    return {
        "documents": documents,
        "metadata": metadata,
        "suggestions": suggestions,
    }


def _unpack_suggestions(query, suggest, keys):
    alternatives = []
    for key in keys:
        for suggestion in getattr(suggest, key, []):
            for option in suggestion.options:
                alternatives.append(
                    (
                        option.score,
                        query[0 : suggestion.offset]
                        + option.text
                        + query[suggestion.offset + suggestion.length :],
                    )
                )
    alternatives.sort(reverse=True)  # highest score first
    return alternatives


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


class APIUserDetailsView(APIView):
    http_method_names = ["get", "put"]
    serializer_class = UserDetailsSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        assert request.user.is_authenticated
        serializer = UserDetailsSerializer(request.user, many=False)
        return Response(serializer.data)

    def put(self, request, format=None):
        user = request.user
        serializer = UserDetailsSerializer(instance=user, data=request.data)
        if serializer.is_valid():
            was_subscribed = user.is_newsletter_subscribed
            old_username = user.username
            serializer.save(user=user)

            if not was_subscribed and user.is_newsletter_subscribed:
                newsletter_subscribed.send(None, user=user)
            if was_subscribed and not user.is_newsletter_subscribed:
                newsletter_unsubscribed.send(None, user=user)

            if old_username != user.username:
                username_changed.send(None, user=user)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


user_details = never_cache(APIUserDetailsView.as_view())


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
