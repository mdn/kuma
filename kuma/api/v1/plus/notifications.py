from __future__ import annotations

import datetime
import json
from typing import Optional

# import requests
import requests
from django.conf import settings
from django.db.models import Q
from django.middleware.csrf import get_token
from ninja import Field, Router
from ninja.pagination import paginate

from kuma.documenturls.models import DocumentURL
from kuma.notifications.models import (
    DefaultWatch,
    Notification,
    NotificationData,
    UserWatch,
    Watch,
)
from kuma.notifications.utils import process_changes
from kuma.settings.common import MAX_NON_SUBSCRIBED
from kuma.users.models import UserProfile

from ..pagination import LimitOffsetPaginatedResponse, LimitOffsetPaginationWithMeta
from ..smarter_schema import Schema

admin_router = Router(tags=["admin"])
notifications_router = Router(tags=["notifications"])
watch_router = Router(tags=["watch"])
limit_offset_paginate_with_meta = paginate(LimitOffsetPaginationWithMeta)


class Ok(Schema):
    ok: bool = True


class WatchUpdateResponse(Schema):
    ok: bool = True
    subscription_limit_reached: bool = False


class NotOk(Schema):
    ok: bool = False
    error: str
    info: dict


class NotificationSchema(Schema):
    id: int
    title: str = Field(..., alias="notification.title")
    text: str = Field(..., alias="notification.text")
    url: str = Field(..., alias="notification.page_url")
    created: datetime.datetime = Field(..., alias="notification.created")
    deleted: bool
    read: bool
    starred: bool


@notifications_router.get(
    "/",
    response=LimitOffsetPaginatedResponse[NotificationSchema],
    url_name="plus.notifications",
)
@limit_offset_paginate_with_meta
def notifications(
    request,
    starred: bool = None,
    unread: bool = None,
    filterType: str = None,
    q: str = None,
    sort: str = None,
    **kwargs,
):
    qs = request.user.notification_set.select_related("notification")
    if starred is not None:
        qs = qs.filter(starred=starred)

    if unread is not None:
        qs = qs.filter(read=not unread)

    if filterType:
        qs = qs.filter(notification__type=filterType)

    if q:
        qs = qs.filter(
            Q(notification__title__icontains=q) | Q(notification__text__icontains=q)
        )

    if sort == "title":
        order_by = "notification__title"
    else:
        order_by = "-notification__created"
    qs = qs.order_by(order_by, "id")

    qs = qs.filter(deleted=False)
    return qs


@notifications_router.post("/all/mark-as-read/", response=Ok)
def mark_all_as_read(request):
    request.user.notification_set.filter(read=False).update(read=True)
    return True


@notifications_router.post("/{int:pk}/mark-as-read/", response=Ok)
def mark_as_read(request, pk: int):
    request.user.notification_set.filter(pk=pk, read=False).update(read=True)
    return True


@notifications_router.post("/{int:pk}/toggle-starred/", response={200: Ok, 400: str})
def toggle_starred(request, pk: int):
    try:
        notification = Notification.objects.get(user=request.user, pk=pk)
    except Notification.DoesNotExist:
        return 400, "no matching notification"
    notification.starred = not notification.starred
    notification.save()
    return 200, True


class StarMany(Schema):
    ids: list[int]


@notifications_router.post(
    "/star-ids/", response={200: Ok, 400: str}, url_name="notifications_star_ids"
)
def star_many(request, data: StarMany):
    request.user.notification_set.filter(deleted=False).filter(pk__in=data.ids).update(
        starred=True
    )
    return 200, True


@notifications_router.post(
    "/unstar-ids/", response={200: Ok, 400: str}, url_name="notifications_unstar_ids"
)
def unstar_many(request, data: StarMany):
    request.user.notification_set.filter(deleted=False).filter(pk__in=data.ids).update(
        starred=False
    )
    return 200, True


@notifications_router.post(
    "/{int:pk}/delete/", response=Ok, url_name="notifications_delete_id"
)
def delete_notification(request, pk: int):
    request.user.notification_set.filter(id=pk).update(deleted=True)
    return True


@notifications_router.post("/{int:pk}/undo-deletion/", response=Ok)
def undo_deletion(request, pk: int):
    request.user.notification_set.filter(id=pk).update(deleted=False)
    return True


class DeleteMany(Schema):
    ids: list[int]


@notifications_router.post(
    "/delete-ids/", response={200: Ok, 400: NotOk}, url_name="notifications_delete_many"
)
def delete_notifications(request, data: DeleteMany):
    request.user.notification_set.filter(deleted=False).filter(pk__in=data.ids).update(
        deleted=True
    )
    return 200, True


class WatchSchema(Schema):
    title: str
    url: str
    path: str


@watch_router.get("/watching/", url_name="watching")
def watched(request, q: str = "", url: str = "", limit: int = 20, offset: int = 0):
    qs = request.user.userwatch_set.select_related("watch", "user__defaultwatch")
    profile: UserProfile = request.auth

    hasDefault = None
    try:
        hasDefault = request.user.defaultwatch.custom_serialize()
    except DefaultWatch.DoesNotExist:
        pass
    if url:
        url = DocumentURL.normalize_uri(url)
        qs = qs.filter(watch__url=url)
    if q:
        qs = qs.filter(watch__title__icontains=q)

    qs = qs[offset : offset + limit]
    response = {}
    results = []
    # Default settings at top level if exist
    if hasDefault:
        response["default"] = hasDefault
    response["csrfmiddlewaretoken"] = get_token(request)
    for item in qs:
        res = {}
        res["title"] = item.watch.title
        res["url"] = item.watch.url
        res["path"] = item.watch.path

        # No custom notifications just major updates.
        if not item.custom:
            res["status"] = "major"
        else:
            res["status"] = "custom"
            # Subscribed to custom
            if item.custom_default and hasDefault:
                # Subscribed to the defaults
                res["custom"] = "default"
            else:
                # Subscribed to fine-grained options
                res["custom"] = item.custom_serialize()
        results.append(res)

    if url != "" and len(results) == 0:
        response["status"] = "unwatched"
    elif len(results) == 1 and url != "":
        response = response | results[0]
    else:
        response["items"] = results
    if not profile.is_subscriber:
        response["subscription_limit_reached"] = (
            request.user.userwatch_set.count() >= MAX_NON_SUBSCRIBED["notification"]
        )
    return response


class UpdateWatchCustom(Schema):
    compatibility: list[str]
    content: bool


class UpdateWatch(Schema):
    unwatch: bool = None
    title: str = None
    path: str = None

    custom: UpdateWatchCustom = None
    custom_default: bool = None
    update_custom_default: bool = False


@watch_router.post(
    "/watching/", response={200: WatchUpdateResponse, 400: NotOk, 400: NotOk}
)
def update_watch(request, url: str, data: UpdateWatch):
    url = DocumentURL.normalize_uri(url)
    profile: UserProfile = request.auth
    watched: Optional[UserWatch] = (
        request.user.userwatch_set.select_related("watch", "user__defaultwatch")
        .filter(watch__url=url)
        .first()
    )
    user = watched.user if watched else request.user
    watched_count = request.user.userwatch_set.count()
    print("watched count %s " % watched_count)
    subscription_limit_reached = watched_count >= MAX_NON_SUBSCRIBED["notification"]

    if data.unwatch:
        if watched:
            watched.delete()
        subscription_limit_reached = (watched_count - 1) >= MAX_NON_SUBSCRIBED[
            "notification"
        ]
        return 200, {
            "subscription_limit_reached": subscription_limit_reached,
            "ok": True,
        }

    title = data.title
    if not title:
        return 400, {"error": "missing title"}

    path = data.path or ""
    watched_data = {"custom": data.custom is not None}

    if data.custom:
        custom_default = bool(data.custom_default)
        watched_data["custom_default"] = custom_default
        custom_data = {
            "content_updates": data.custom.content,
        }
        custom_data["browser_compatibility"] = sorted(data.custom.compatibility)
        if custom_default:
            try:
                default_watch = user.defaultwatch
                if data.update_custom_default:
                    for key, value in custom_data.items():
                        setattr(default_watch, key, value)
                    default_watch.save()
            except DefaultWatch.DoesNotExist:
                # Always create custom defaults if they are missing.
                DefaultWatch.objects.update_or_create(user=user, defaults=custom_data)
        watched_data.update(custom_data)
    if watched:
        watch: Watch = watched.watch
        # Update the title / path if they changed.
        if title != watch.title or path != watch.path:
            watch.title = title
            watch.path = path
            watch.save()
    else:
        # Check on creation if allowed.
        if (
            watched_count >= MAX_NON_SUBSCRIBED["notification"]
            and not profile.is_subscriber
        ):
            return 400, {
                "error": "max_subscriptions",
                "info": {"max_allowed": MAX_NON_SUBSCRIBED["notification"]},
            }
        watch = Watch.objects.get_or_create(url=url, title=title, path=path)[0]
        subscription_limit_reached = (watched_count + 1) >= MAX_NON_SUBSCRIBED[
            "notification"
        ]
    user.userwatch_set.update_or_create(watch=watch, defaults=watched_data)
    return 200, {"subscription_limit_reached": subscription_limit_reached, "ok": True}


class UnwatchMany(Schema):
    unwatch: list[str]


@watch_router.post(
    "/unwatch-many/",
    response={200: WatchUpdateResponse, 400: NotOk},
    url_name="unwatch_many",
)
def unwatch(request, data: UnwatchMany):

    request.user.userwatch_set.select_related("watch", "user__watch").filter(
        watch__url__in=data.unwatch
    ).delete()
    profile: UserProfile = request.auth
    if not profile.is_subscriber:
        subscription_limit_reached = (
            request.user.userwatch_set.count() >= MAX_NON_SUBSCRIBED["notification"]
        )

    return 200, {"subscription_limit_reached": subscription_limit_reached, "ok": True}


class CreateNotificationSchema(Schema):
    raw_url: str = Field(..., alias="page")
    title: str
    text: str


@admin_router.post("/create/", response={200: Ok, 400: NotOk})
def create(request, body: CreateNotificationSchema):
    url = DocumentURL.normalize_uri(body.raw_url)
    watchers = Watch.objects.filter(url=url)
    if not watchers:
        return 400, {"error": "No watchers found"}
    notification_data, _ = NotificationData.objects.get_or_create(
        text=body.text, title=body.title, type="content"
    )

    for watcher in watchers:
        # considering the possibility of multiple pages existing for the same path
        for user in watcher.users.all():
            Notification.objects.create(notification=notification_data, user=user)

    return True


class UpdateNotificationSchema(Schema):
    filename: str


@admin_router.post("/update/", response={200: Ok, 400: NotOk, 401: NotOk})
def update(request, body: UpdateNotificationSchema):
    try:
        changes = json.loads(
            requests.get(settings.NOTIFICATIONS_CHANGES_URL + body.filename).content
        )
    except Exception:
        return 400, {"error": "Error while processing file"}

    try:
        process_changes(changes)
    except Exception:
        return 400, {"ok": False, "error": "Error while processing file"}

    return 200, True


class CreatePRNotificationSchema(Schema):
    raw_url: str = Field(..., alias="page")
    repo: str = Field(..., alias="repo")
    pr: int


@admin_router.post("/create/pr/", response={200: Ok, 400: NotOk, 401: NotOk})
def create_pr(request, body: CreatePRNotificationSchema):
    url = DocumentURL.normalize_uri(body.raw_url)
    watchers = Watch.objects.filter(url=url)
    if not watchers:
        return 400, {"error": "No watchers found"}

    content = f"Page updated (see PR!{body.repo.strip('/')}!{body.pr}!!)"
    notification_data, _ = NotificationData.objects.get_or_create(
        text=content, title=watchers[0].title, type="content"
    )

    for watcher in watchers:
        # considering the possibility of multiple pages existing for the same path
        for user in watcher.users.all():
            Notification.objects.create(notification=notification_data, user=user)

    return 200, True
