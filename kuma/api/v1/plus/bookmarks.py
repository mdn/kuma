import functools

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from kuma.api.v1.decorators import require_subscriber
from kuma.bookmarks.models import Bookmark
from kuma.documenturls.models import DocumentURL, download_url


class NotOKDocumentURLError(Exception):
    """When the document URL doesn't resolve as a 200 OK"""


@never_cache
@require_http_methods(["GET", "POST"])
@require_subscriber
def bookmarks(request):
    # E.g. POST -d url=https://... /api/v1/bookmarks/
    if request.method == "POST":
        return _toggle_bookmark(request)

    # E.g GET /api/v1/bookmarks/?url=https://...
    elif request.GET.get("url"):
        return _get_bookmark(request)

    # E.g. GET /api/v1/bookmarks/
    return _get_bookmarks(request)


def _get_bookmarks(request):
    try:
        page = int(request.GET.get("page") or "1")
        assert page > 0 and page < 100
    except (ValueError, AssertionError):
        return HttpResponseBadRequest("invalid 'page'")
    try:
        per_page = int(
            request.GET.get("per_page") or settings.API_V1_BOOKMARKS_PAGE_SIZE
        )
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


def valid_url(url):
    return (
        url.startswith("/")
        and ("/docs/" in url or "/plus/" in url)
        and "://" not in url
    )


def get_url(view_function):
    @functools.wraps(view_function)
    def inner(request, *args, **kwargs):
        url = (
            (request.GET.get("url") or "")
            .strip()
            .replace("https://developer.mozilla.org", "")
        )
        if not url:
            return HttpResponseBadRequest("missing 'url'")
        if not valid_url(url):
            return HttpResponseBadRequest("invalid 'url'")

        return view_function(request, *(args + (url,)), **kwargs)

    return inner


@get_url
def _get_bookmark(request, url):

    users_bookmarks = Bookmark.objects.filter(
        user_id=request.user.id, deleted__isnull=True
    )
    bookmarked = None
    for bookmark in users_bookmarks.filter(
        documenturl__uri=DocumentURL.normalize_uri(url)
    ):
        bookmarked = {"id": bookmark.id, "created": bookmark.created}

    context = {
        "bookmarked": bookmarked,
        "csrfmiddlewaretoken": get_token(request),
    }
    return JsonResponse(context)


@get_url
def _toggle_bookmark(request, url):
    absolute_url = f"{settings.BOOKMARKS_BASE_URL}{url}/index.json"
    try:
        documenturl = DocumentURL.objects.get(uri=DocumentURL.normalize_uri(url))
        assert not documenturl.invalid
    except DocumentURL.DoesNotExist:
        response = download_url(absolute_url)
        # Because it's so big, only store certain fields that are used.
        full_metadata = response.json()["doc"]
        metadata = {}
        # Should we so day realize that we want to and need to store more
        # about the remote Yari documents, we'd simply invoke some background
        # processing job that forces a refresh.
        for key in ("title", "mdn_url", "parents"):
            if key in full_metadata:
                metadata[key] = full_metadata[key]

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

            # If a user deletes a bookmark and then decides to bookmark it again
            # it's because they used the "undo" functionality in the front-end.
            # If this is the case, the most recently modified bookmark is going
            # to be the one they deleted.
            was_undo = False
            for most_recently_modified in Bookmark.objects.filter(
                user_id=request.user.id,
            ).order_by("-modified")[:1]:
                was_undo = most_recently_modified.id == bookmark.id
            if not was_undo:
                # When you undo, it doesn't change the 'created' date.
                # But if you've re-bookmarked it after some time
                bookmark.created = timezone.now()
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

    return JsonResponse({"OK": True}, status=201)
