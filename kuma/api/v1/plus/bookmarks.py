from datetime import datetime
from typing import Optional, Union

from django.conf import settings
from django.db.models import Case, CharField, F, Q, When
from django.db.models.functions import Cast
from django.middleware.csrf import get_token
from django.utils import timezone
from ninja import Field, Form, Query, Router
from pydantic import validator

from kuma.api.v1.plus.notifications import NotOk, Ok
from kuma.api.v1.smarter_schema import Schema
from kuma.bookmarks.models import Bookmark
from kuma.documenturls.models import DocumentURL, download_url
from kuma.users.models import UserProfile

from ..pagination import (
    PageNumberPaginationWithMeta,
    PaginatedResponse,
    PaginationInput,
)


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


class CollectionPaginatedInput(PaginationInput):
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
    "",
    response=Union[PaginatedResponse[CollectionItemSchema], CollectionItemResponse],
    summary="Get collection",
    url_name="collections",
)
def bookmarks(request, filters: CollectionPaginatedInput = Query(...)):
    """
    If `url` is passed, return that specific collection item, otherwise return
    a paginated list of collection items.
    """
    user = request.user

    # Single bookmark request.
    if filters.url:
        bookmark: Optional[Bookmark] = user.bookmark_set.filter(
            documenturl__uri=DocumentURL.normalize_uri(filters.url), deleted=None
        ).first()
        return {
            "bookmarked": bookmark,
            "csrfmiddlewaretoken": get_token(request),
        }

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

    paginator = PageNumberPaginationWithMeta()
    return paginator.paginate_queryset(qs, request, pagination=filters)


@router.post(
    "",
    response={200: Ok, 201: Ok, 400: NotOk},
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

    if delete:
        if bookmark and not bookmark.deleted:
            bookmark.deleted = timezone.now()
            bookmark.save()
        return 200, True

    profile: UserProfile = request.auth
    if (
        not profile.is_subscriber
        and request.user.bookmark_set.filter(deleted=None).count() > 2
    ):
        return 400, {"error": "max_subscriptions"}

    if bookmark:
        bookmark.deleted = None

        # If a user deletes a bookmark and then decides to bookmark it again
        # it's because they used the "undo" functionality in the front-end.
        # If this is the case, the most recently modified bookmark is going
        # to be the one they deleted.
        most_recently_deleted: Optional[Bookmark] = (
            request.user.bookmark_set.exclude(deleted=None).order_by("modified").last()
        )
        was_undo = most_recently_deleted and most_recently_deleted.pk == bookmark.pk
        if not was_undo:
            # When you undo, it doesn't change the 'created' date.
            # But if you've re-bookmarked it after some time
            bookmark.created = timezone.now()
    else:
        # Otherwise, create a brand new entry
        bookmark = request.user.bookmark_set.create(documenturl=documenturl)

    if name is not None:
        bookmark.custom_name = name[:500]
    if notes is not None:
        bookmark.notes = notes[:500]
    bookmark.save()

    return 201, True
