from __future__ import annotations

import datetime
import json
from typing import Optional

# import requests
from django.db.models import Q
from ninja import Field, Router
from ninja.pagination import paginate

from kuma.api.v1.auth import is_notifications_admin
from kuma.api.v1.decorators import require_subscriber
from kuma.notifications.models import (
    DefaultWatch,
    Notification,
    NotificationData,
    UserWatch,
    Watch,
)
from kuma.notifications.utils import process_changes

from ..smarter_schema import Schema
from ..pagination import PageNumberPaginationWithMeta, PaginatedSchema

notifications_router = Router(tags=["notifications"])
watch_router = Router(tags=["collection"])
paginate_with_meta = paginate(PageNumberPaginationWithMeta)


class Ok(Schema):
    ok: bool = True


class NotOk(Schema):
    ok: bool = False
    error: str


class NotificationSchema(Schema):
    id: int
    title: str = Field(..., alias="notification.title")
    text: str = Field(..., alias="notification.text")
    url: str = Field(..., alias="notification.page_url")
    created: datetime.datetime = Field(..., alias="notification.created")
    read: bool
    starred: bool


@notifications_router.get(
    "/",
    response=PaginatedSchema[NotificationSchema],
    url_name="plus.notifications",
)
@paginate_with_meta
def notifications(
    request,
    starred: bool = None,
    filterType: str = None,
    q: str = None,
    sort: str = None,
    **kwargs,
):
    qs = request.user.notification_set.select_related("notification")
    if starred is not None:
        qs = qs.filter(starred=starred)

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
    qs = qs.order_by(order_by)

    return qs


class WatchSchema(Schema):
    title: str
    url: str
    path: str


@watch_router.get("/watched/", response=PaginatedSchema[WatchSchema])
@paginate_with_meta
def watched(request, q: str = "", **kwargs):
    qs = Watch.objects.filter(users=request.user.id).order_by("title")
    if q:
        qs = qs.filter(title__icontains=q)
    return qs


@notifications_router.get("/all/mark-as-read/", response=Ok)
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


@notifications_router.post("/{int:pk}/delete/", response=Ok)
def delete_notification(request, pk: int):
    request.user.notification_set.filter(id=pk).delete()
    return True


@watch_router.get("/watch{path:url}")
@require_subscriber
def watch(request, url):
    # E.g.GET /api/v1/notifications/watch/en-US/docs/Web/CSS/
    watched: Optional[UserWatch] = (
        request.user.userwatch_set.select_related("watch", "user__defaultwatch")
        .filter(watch__url=url)
        .first()
    )
    user = watched.user if watched else request.user

    response = {"ok": True}
    try:
        response["default"] = user.defaultwatch.custom_serialize()
    except DefaultWatch.DoesNotExist:
        pass

    if watched:
        if not watched.custom:
            response["status"] = "major"
        else:
            response["status"] = "custom"
            if watched.custom_default and "default" in response:
                response["custom"] = True
            else:
                response["custom"] = watched.custom_serialize()
    else:
        response["status"] = "unwatched"

    return response


class UpdateWatch(Schema):
    unwatch: bool = None
    title: str = None
    path: str = None

    custom: bool = None
    content: str = None
    custom_default: bool = None
    update_custom_default: bool = None
    compatibility: list[str] = None


@watch_router.post("/watch{path:url}", response={200: Ok, 400: NotOk})
def update_watch(request, url, data: UpdateWatch):
    watched: Optional[UserWatch] = (
        request.user.userwatch_set.select_related("watch", "user__defaultwatch")
        .filter(watch__url=url)
        .first()
    )
    user = watched.user if watched else request.user

    if data.unwatch:
        if watched:
            watched.delete()
        return 200, True

    title = data.title
    if not title:
        return 400, {"error": "missing title"}

    path = data.path or ""
    custom = data.custom is not None
    watched_data = {"custom": custom}
    if custom:
        custom_default = bool(data.custom_default)
        watched_data["custom_default"] = custom_default
        update_custom_default = data.get("update_custom_default")
        custom_data = {
            "content_updates": bool(data.content),
        }
        if not isinstance(data.compatibility, list):
            return 400, {"error": "bad compatibility list"}
        custom_data["browser_compatibility"] = sorted(data.compatibility)
        if custom_default:
            try:
                default_watch = user.defaultwatch
                if update_custom_default:
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
        watch = Watch.objects.get_or_create(url=url, title=title, path=path)[0]
    user.userwatch_set.update_or_create(watch=watch, defaults=watched_data)
    return 200, True


class CreateNotificationSchema(Schema):
    page: int
    title: str
    text: str


@notifications_router.post("/create/", auth=is_notifications_admin, response=Ok)
def create(request, body: CreateNotificationSchema):
    watchers = Watch.objects.filter(url=body.page)
    notification_data, _ = NotificationData.objects.get_or_create(
        text=body.text, title=body.title, type="content"
    )
    for watcher in watchers:
        # considering the possibility of multiple pages existing for the same path
        for user in watcher.users.all():
            Notification.objects.create(notification=notification_data, user=user)

    return True


@notifications_router.post(
    "/update/", auth=is_notifications_admin, response={200: Ok, 400: NotOk}
)
def update(request):
    # ToDo: Fetch file from S3
    changes = json.loads("{}")

    try:
        process_changes(changes)
    except Exception:
        return 400, {"error": "Error while processing file"}

    return True
