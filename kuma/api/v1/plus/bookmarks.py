import functools

import requests
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit

from kuma.users.models import UserSubscription


BASE_URL = "http://docker.for.mac.host.internal:5000"

_hacky_cache = {}
_hacky_documents = {}


class NotOKDocumentURLError(Exception):
    """When the document URL doesn't resolve as a 200 OK"""


def is_subscriber(func):
    @functools.wraps(func)
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden("not signed in")
        if not UserSubscription.objects.filter(
            user=user, canceled__isnull=True
        ).exists():
            return HttpResponseForbidden("not a subscriber")
        return func(request, *args, **kwargs)

    return inner


@never_cache
@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["GET"])
@is_subscriber
def bookmarks(request):

    users_bookmarks = _hacky_cache.get(request.user.id, set())
    # Return all in sorted order
    items = sorted(users_bookmarks, key=lambda b: b["created"], reverse=True)
    for item in items:
        item["title"] = _hacky_documents[item["url"]]["title"]

    context = {
        "items": items,
        "count": len(items),
    }
    context["csrfmiddlewaretoken"] = get_token(request)
    return JsonResponse(context)


@never_cache
@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["GET", "POST"])
def bookmarked(request):

    url = (
        (request.GET.get("url") or "")
        .strip()
        .replace("https://developer.mozilla.org", "")
    )
    if not url:
        return HttpResponseBadRequest("missing 'url'")
    if not valid_url(url):
        return HttpResponseBadRequest("invalid 'url'")

    get_document_from_url(url)

    users_bookmarks = _hacky_cache.get(request.user.id, [])

    if request.method == "POST":
        # Let's toggle
        if url in [x["url"] for x in users_bookmarks]:
            users_bookmarks = [x for x in users_bookmarks if x["url"] != url]
        else:
            now = convert_to_utc(timezone.now())
            users_bookmarks.append(
                {
                    "id": users_bookmarks
                    and max(b["id"] for b in users_bookmarks) + 1
                    or 1,
                    "created": now,
                    "url": url,
                }
            )
        _hacky_cache[request.user.id] = users_bookmarks
        return JsonResponse({"OK": True})
    else:
        # Query
        try:
            bookmarked = [b for b in users_bookmarks if b["url"] == url][0]["created"]
        except IndexError:
            bookmarked = None
        context = {
            "bookmarked": bookmarked,
            "csrfmiddlewaretoken": get_token(request),
        }
        return JsonResponse(context)


def convert_to_utc(dt):
    """
    Given a timezone naive or aware datetime return it converted to UTC.
    """
    # Check if the given dt is timezone aware and if not make it aware.
    if timezone.is_naive(dt):
        default_timezone = timezone.get_default_timezone()
        dt = timezone.make_aware(dt, default_timezone)

    # Convert the datetime to UTC.
    return dt.astimezone(timezone.utc)


def valid_url(url):
    return url.startswith("/") and ("/docs/" in url or "/plus/" in url)


def get_document_from_url(url):
    if url not in _hacky_documents:
        abs_url = f"{BASE_URL}{url}/index.json"
        r = requests.get(abs_url, allow_redirects=False)
        if r.status_code != 200:
            raise NotOKDocumentURLError(abs_url)
        r.raise_for_status()
        data = r.json()
        _hacky_documents[url] = data["doc"]
    return _hacky_documents[url]
