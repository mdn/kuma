import functools


from django.conf import settings
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

from kuma.bookmarks.models import Bookmark
from kuma.documenturls.models import DocumentURL, download_url
from kuma.users.models import UserSubscription


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

    try:
        page = int(request.GET.get("page") or "1")
        assert page > 0 and page < 100
    except (ValueError, AssertionError):
        return HttpResponseBadRequest("invalid 'page'")
    try:
        per_page = int(request.GET.get("per_page") or "30")
        assert per_page > 0 and per_page <= 100
    except (ValueError, AssertionError):
        return HttpResponseBadRequest("invalid 'per_page'")

    users_bookmarks = Bookmark.objects.filter(
        user_id=request.user.id, deleted__isnull=True
    ).order_by("-created")

    def serialize_bookmarks(qs):
        for bookmark in qs.select_related("documenturl"):
            # In Yari, the `metadata["parents"]` will always include "self"
            # in the last link. Omit that here.
            parents = bookmark.documenturl.metadata.get("parents", [])[:-1]
            yield {
                "id": bookmark.id,
                "url": bookmark.documenturl.metadata["mdn_url"],
                "title": bookmark.documenturl.metadata["title"],
                "parents": parents,
                "created": bookmark.created,
            }

    m = (page - 1) * per_page
    n = page * per_page
    context = {
        "items": list(serialize_bookmarks(users_bookmarks[m:n])),
        "metadata": {
            "total": users_bookmarks.count(),
            "page": page,
            "per_page": per_page,
        },
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
        return HttpResponseBadRequest("invalid 'url'") and "://" not in url

    absolute_url = f"{settings.BOOKMARKS_BASE_URL}{url}/index.json"

    if request.method == "POST":
        # Let's toggle!
        try:
            documenturl = DocumentURL.objects.get(uri=DocumentURL.normalize_uri(url))
            assert not documenturl.invalid
        except DocumentURL.DoesNotExist:
            response = download_url(absolute_url)
            metadata = response.json()["doc"]
            # Because it's so big, don't store certain fields that are
            # not helpful.
            metadata.pop("body", None)
            metadata.pop("toc", None)
            metadata.pop("sidebarHTML", None)
            metadata.pop("other_translations", None)
            metadata.pop("flaws", None)
            documenturl = DocumentURL.objects.create(
                uri=DocumentURL.normalize_uri(url),
                absolute_url=absolute_url,
                metadata=metadata,
            )

        users_bookmarks = Bookmark.objects.filter(
            user_id=request.user.id, documenturl=documenturl
        )

        for bookmark in users_bookmarks:
            # If had a bookmark before, only need to toggle the 'deleted'
            if bookmark.deleted:
                bookmark.deleted = None
            else:
                bookmark.deleted = timezone.now()
            bookmark.save()
            break
        else:
            # Otherwise, create a brand new entry
            Bookmark.objects.create(
                user_id=request.user.id,
                documenturl=documenturl,
            )

        return JsonResponse({"OK": True})
    else:

        def serialize_bookmark(bookmark):
            return {"id": bookmark.id, "created": bookmark.created}

        # raise Exception(url)
        users_bookmarks = Bookmark.objects.filter(
            user_id=request.user.id, deleted__isnull=True
        )
        bookmarked = None
        for bookmark in users_bookmarks.filter(
            documenturl__uri=DocumentURL.normalize_uri(url)
        ):
            bookmarked = serialize_bookmark(bookmark)

        context = {
            "bookmarked": bookmarked,
            "csrfmiddlewaretoken": get_token(request),
        }
        return JsonResponse(context)


def valid_url(url):
    return (
        url.startswith("/")
        and ("/docs/" in url or "/plus/" in url)
        and "://" not in url
    )
