from datetime import datetime
from typing import Optional, Union

from django.conf import settings
from django.db.models import Case, CharField, F, Q, When
from django.db.models.functions import Cast
from django.middleware.csrf import get_token
from django.utils import timezone
from ninja import Field, Form, Query, Router
from pydantic import validator

from kuma.api.v1.plus.notifications import NotOk
from kuma.api.v1.smarter_schema import Schema
from kuma.bookmarks.models import Bookmark
from kuma.documenturls.models import DocumentURL, download_url
from kuma.settings.common import MAX_NON_SUBSCRIBED
from kuma.users.models import UserProfile


class LimitOffsetInput(Schema):
    limit: int = Field(20, gt=0)
    offset: int = Field(0, ge=1)


class NotOKDocumentURLError(Exception):
    """When the document URL doesn't resolve as a 200 OK"""


router = Router(tags=["collection"])


class CollectionParent(Schema):
    uri: str
    title: str


class CollectionItemSchema(Schema):
    id: int
    url: str
    title: str
    notes: str
    parents: list[CollectionParent]
    created: datetime

    @staticmethod
    def resolve_url(bookmark):
        return bookmark.documenturl.metadata["mdn_url"]

    @staticmethod
    def resolve_parents(bookmark):
        return bookmark.documenturl.metadata.get("parents", [])[:-1]


class CollectionItemResponse(Schema):
    bookmarked: Optional[CollectionItemSchema]
    csrfmiddlewaretoken: str
    subscription_limit_reached: Optional[bool]


class MultipleCollectionItemResponse(Schema):
    items: list[CollectionItemSchema]
    csrfmiddlewaretoken: str
    subscription_limit_reached: Optional[bool]


class CollectionUpdateResponse(Schema):
    subscription_limit_reached: Optional[bool]
    ok: bool


class CollectionPaginatedInput(LimitOffsetInput):
    url: str = None
    terms: str = Field(None, alias="q")
    sort: str = None

    @validator("url")
    def valid_bookmark_url(cls, url):
        url = url.strip().replace("https://developer.mozilla.org", "")
        assert (
            url.startswith("/")
            and ("/docs/" in url or "/plus/" in url)
            and "://" not in url
        ), "invalid collection item url"
        return url


@router.get(
    "/",
    response=Union[MultipleCollectionItemResponse, CollectionItemResponse],
    summary="Get collection",
    url_name="collections",
)
def bookmarks(request, filters: CollectionPaginatedInput = Query(...)):
    """
    If `url` is passed, return that specific collection item, otherwise return
    a paginated list of collection items.
    """
    user = request.user
    profile: UserProfile = request.auth

    # Single bookmark request.
    if filters.url:
        bookmark: Optional[Bookmark] = user.bookmark_set.filter(
            documenturl__uri=DocumentURL.normalize_uri(filters.url), deleted=None
        ).first()
        response = {"bookmarked": bookmark, "csrfmiddlewaretoken": get_token(request)}
        if not profile.is_subscriber:
            response["subscription_limit_reached"] = (
                user.bookmark_set.filter(deleted=None).count()
                >= MAX_NON_SUBSCRIBED["collection"]
            )

        return response

    # Otherwise return a paginated list of bookmarks.
    qs = (
        Bookmark.objects.filter(user_id=user.id, deleted__isnull=True)
        .select_related("documenturl")
        .order_by("-created")
    )

    if filters.sort == "title" or filters.terms:
        qs = qs.annotate(
            display_title=Case(
                When(
                    custom_name="",
                    then=Cast("documenturl__metadata__title", CharField()),
                ),
                default=F("custom_name"),
            )
        )

    if filters.sort == "title":
        qs = qs.order_by("display_title")

    if filters.terms:
        qs = qs.filter(
            Q(display_title__icontains=filters.terms)
            | Q(notes__icontains=filters.terms)
        )
    response = {}
    response["csrfmiddlewaretoken"] = get_token(request)
    qs = qs[filters.offset : filters.offset + filters.limit]
    response["items"] = []
    for item in qs:
        response["items"].append(item)
    if not profile.is_subscriber:
        response["subscription_limit_reached"] = (
            user.bookmark_set.filter(deleted=None).count()
            >= MAX_NON_SUBSCRIBED["collection"]
        )
    return response


@router.post(
    "/",
    response={200: CollectionUpdateResponse, 201: CollectionUpdateResponse, 400: NotOk},
    summary="Save or delete a collection item",
)
def save_or_delete_bookmark(
    request,
    url,
    delete: bool = Form(None),
    name: str = Form(None),
    notes: str = Form(None),
):
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

    bookmark_count = request.user.bookmark_set.filter(deleted=None).count()
    if delete:
        if bookmark and not bookmark.deleted:
            bookmark.deleted = timezone.now()
            bookmark.save()
            # Having deleted it's unlikely that the limit will still be reached but check anyway.
            subscription_limit_reached = (bookmark_count - 1) >= MAX_NON_SUBSCRIBED[
                "collection"
            ]
        return 200, {
            "subscription_limit_reached": subscription_limit_reached,
            "ok": True,
        }

    profile: UserProfile = request.auth
    subscription_limit_reached = bookmark_count >= MAX_NON_SUBSCRIBED["collection"]

    # Update logic
    if bookmark and not bookmark.deleted:
        if name is not None:
            bookmark.custom_name = name[:500]
        if notes is not None:
            bookmark.notes = notes[:500]
        bookmark.save()
        return 201, {
            "subscription_limit_reached": subscription_limit_reached
            and not profile.is_subscriber,
            "ok": True,
        }

    # Create or undelete. Check limits.
    if not profile.is_subscriber and subscription_limit_reached:
        return 400, {
            "error": "max_subscriptions",
            "info": {"max_allowed": MAX_NON_SUBSCRIBED["collection"]},
        }

    # If found undelete
    if bookmark:
        bookmark.deleted = None
    else:
        # Otherwise, create a brand new entry
        bookmark = request.user.bookmark_set.create(documenturl=documenturl)

    if name is not None:
        bookmark.custom_name = name[:500]
    if notes is not None:
        bookmark.notes = notes[:500]

    bookmark.save()
    subscription_limit_reached = (
        bookmark_count + 1 >= MAX_NON_SUBSCRIBED["collection"]
        and not profile.is_subscriber
    )
    return 201, {"subscription_limit_reached": subscription_limit_reached, "ok": True}
