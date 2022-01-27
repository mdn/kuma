import functools
from typing import Optional

from django.conf import settings
from django.db.models import Case, CharField, F, Q, When
from django.db.models.functions import Cast
from django.http import HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from kuma.api.v1.decorators import require_subscriber
from kuma.api.v1.plus import api_list, ItemGenerationData
from kuma.bookmarks.models import Bookmark
from kuma.documenturls.models import DocumentURL, download_url
from kuma.users.models import UserProfile


class NotOKDocumentURLError(Exception):
    """When the document URL doesn't resolve as a 200 OK"""


@never_cache
@require_http_methods(["GET", "POST"])
@require_subscriber
def bookmarks(request):
    # E.g. POST -d url=https://... /api/v1/bookmarks/
    if request.method == "POST":
        return _save_or_delete_bookmark(request)

    # E.g GET /api/v1/bookmarks/?url=https://...
    elif request.GET.get("url"):
        return _get_bookmark(request)

    # E.g. GET /api/v1/bookmarks/
    return _get_bookmarks(request)


def serialize_bookmark(bookmark: Bookmark):
    parents = bookmark.documenturl.metadata.get("parents", [])[:-1]
    return {
        "id": bookmark.id,
        "url": bookmark.documenturl.metadata["mdn_url"],
        "title": bookmark.title,
        "notes": bookmark.notes,
        "parents": parents,
        "created": bookmark.created,
    }


@api_list
def _get_bookmarks(request) -> ItemGenerationData:
    qs = (
        Bookmark.objects.filter(user_id=request.user.id, deleted__isnull=True)
        .select_related("documenturl")
        .order_by("-created")
    )

    terms = request.GET.get("q")

    if request.GET.get("sort") == "title" or terms:

        qs = qs.annotate(
            display_title=Case(
                When(
                    custom_name="",
                    then=Cast("documenturl__metadata__title", CharField()),
                ),
                default=F("custom_name"),
            )
        )

    if request.GET.get("sort") == "title":
        qs = qs.order_by("display_title")

    if terms:
        qs = qs.filter(Q(display_title__icontains=terms) | Q(notes__icontains=terms))

    return qs, serialize_bookmark


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
    bookmark: Optional[Bookmark] = request.user.bookmark_set.filter(
        documenturl__uri=DocumentURL.normalize_uri(url), deleted=None
    ).first()
    context = {
        "bookmarked": bookmark and serialize_bookmark(bookmark),
        "csrfmiddlewaretoken": get_token(request),
    }
    return JsonResponse(context)


@get_url
def _save_or_delete_bookmark(request, url):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None

    if not profile:
        return JsonResponse({"OK": False, "error": "not_logged_in"}, status=400)

    if not profile.is_subscriber and request.user.bookmark_set.count() > 2:
        return JsonResponse({"OK": False, "error": "max_subscriptions"}, status=400)

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

    bookmark: Optional[Bookmark] = request.user.bookmark_set.filter(
        documenturl=documenturl
    ).first()

    if "delete" in request.POST:
        if bookmark and not bookmark.deleted:
            bookmark.deleted = timezone.now()
            bookmark.save()
    else:
        if bookmark:
            bookmark.deleted = None

            # If a user deletes a bookmark and then decides to bookmark it again
            # it's because they used the "undo" functionality in the front-end.
            # If this is the case, the most recently modified bookmark is going
            # to be the one they deleted.
            most_recently_deleted: Optional[Bookmark] = (
                request.user.bookmark_set.exclude(deleted=None)
                .order_by("modified")
                .last()
            )
            was_undo = most_recently_deleted and most_recently_deleted.pk == bookmark.pk
            if not was_undo:
                # When you undo, it doesn't change the 'created' date.
                # But if you've re-bookmarked it after some time
                bookmark.created = timezone.now()
        else:
            # Otherwise, create a brand new entry
            bookmark = request.user.bookmark_set.create(documenturl=documenturl)
        if "name" in request.POST:
            bookmark.custom_name = (request.POST["name"] or "")[:500]
            bookmark.notes = (request.POST.get("notes") or "")[:500]
        bookmark.save()

    return JsonResponse({"OK": True}, status=201)
