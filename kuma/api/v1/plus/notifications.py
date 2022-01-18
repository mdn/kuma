from __future__ import annotations

import json
from typing import Optional

import requests
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from kuma.api.v1.decorators import require_subscriber
from kuma.api.v1.plus import ItemGenerationData, api_list
from kuma.notifications.models import (
    DefaultWatch,
    Notification,
    NotificationData,
    UserWatch,
    Watch,
)
from kuma.notifications.utils import process_changes


@never_cache
@require_http_methods(["GET"])
@require_subscriber
def notifications(request):
    # E.g. GET /api/v1/notifications/
    return _notification_list(request)


@api_list
def _notification_list(request) -> ItemGenerationData:
    qs = request.user.notification_set.select_related("notification")

    if "filterStarred" in request.GET:
        qs = qs.filter(
            starred=any(i == request.GET.get("filterStarred") for i in ["true", "True"])
        )

    type = request.GET.get("filterType")
    if type:
        qs = qs.filter(notification__type=type)

    terms = request.GET.get("q")
    if terms:
        qs = qs.filter(
            Q(notification__title__icontains=terms)
            | Q(notification__text__icontains=terms)
        )

    sort = request.GET.get("sort")
    if sort == "title":
        order_by = "notification__title"
    else:
        order_by = "-notification__created"
    qs = qs.order_by(order_by)

    return (
        qs,
        lambda notification: notification.serialize(),
    )


@never_cache
@require_http_methods(["GET"])
@require_subscriber
def watched(request):
    # E.g. GET /api/v1/notifications/
    return _watched_list(request)


@api_list
def _watched_list(request) -> ItemGenerationData:
    qs = Watch.objects.filter(users=request.user.id).order_by("title")
    search = request.GET.get("q")
    if search:
        qs = qs.filter(title__icontains=search)
    return (qs, lambda obj: obj.serialize())


@never_cache
@require_http_methods(["POST"])
@require_subscriber
def mark_as_read(request, id: int | str):
    # E.g.POST /api/v1/notifications/<id>/mark-as-read/
    kwargs = dict(user=request.user, read=False)

    if isinstance(id, int):
        kwargs["id"] = id

    unread = Notification.objects.filter(**kwargs)
    if isinstance(id, int) and not unread:
        return HttpResponseBadRequest("invalid 'id'")

    unread.update(read=True)
    return JsonResponse({"OK": True}, status=200)


@never_cache
@require_http_methods(["POST"])
@require_subscriber
def toggle_starred(request, id: int):
    # E.g.POST /api/v1/notifications/<id>/toggle-starred/
    try:
        notification = Notification.objects.get(user=request.user, id=id)
    except Notification.DoesNotExist:
        return HttpResponseBadRequest("invalid 'id'")

    notification.starred = not notification.starred
    notification.save()
    return JsonResponse({"OK": True}, status=200)


@never_cache
@require_http_methods(["POST"])
@require_subscriber
def delete_notification(request, id: int):
    # E.g.POST /api/v1/notifications/<id>/delete/
    request.user.notification_set.filter(id=id).delete()
    return JsonResponse({"OK": True}, status=200)


@never_cache
@require_http_methods(["GET", "POST"])
@require_subscriber
def watch(request, url):
    # E.g.GET /api/v1/notifications/watch/en-US/docs/Web/CSS/
    watched: Optional[UserWatch] = (
        request.user.userwatch_set.select_related("watch", "user__defaultwatch")
        .filter(watch__url=url)
        .first()
    )
    user = watched.user if watched else request.user

    if request.method == "GET":
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

        return JsonResponse(response, status=200)

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("UTF-8"))
        except Exception:
            return JsonResponse({"ok": False, "error": "bad data"}, status=400)

        if data.get("unwatch"):
            if watched:
                watched.delete()
            return JsonResponse({"ok": True}, status=200)

        title = data.get("title", None)
        if not title:
            return JsonResponse({"ok": False, "error": "missing title"}, status=400)
        path = data.get("path", "")
        custom = "content" in data
        watched_data = {"custom": custom}
        if custom:
            custom_default = bool(data.get("custom_default"))
            watched_data["custom_default"] = custom_default
            update_custom_default = data.get("update_custom_default")
            custom_data = {
                "content_updates": bool(data.get("content")),
            }
            if not isinstance(data.get("compatibility"), list):
                return JsonResponse(
                    {"ok": False, "error": "bad compatibility list"}, status=400
                )
            custom_data["browser_compatibility"] = sorted(data["compatibility"])
            if custom_default:
                try:
                    default_watch = user.defaultwatch
                    if update_custom_default:
                        for key, value in custom_data.items():
                            setattr(default_watch, key, value)
                        default_watch.save()
                except DefaultWatch.DoesNotExist:
                    # Always create custom defaults if they are missing.
                    DefaultWatch.objects.update_or_create(
                        user=user, defaults=custom_data
                    )
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
        return JsonResponse({"ok": True}, status=200)

    return JsonResponse({"ok": False}, status=403)


@never_cache
@require_http_methods(["POST"])
def create(request):
    # E.g.GET /api/v1/notifications/create/
    auth = request.headers.get("Authorization")
    if not auth or auth != settings.NOTIFICATIONS_ADMIN_TOKEN:
        return JsonResponse({"ok": False, "error": "not authorized"}, status=401)

    try:
        data = json.loads(request.body.decode("UTF-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "bad data"}, status=400)

    page = data.get("page", "")
    if not page:
        return JsonResponse({"ok": False, "error": "missing page"}, status=400)

    title = data.get("title", "")
    text = data.get("text", "")

    if not title or not text:
        return JsonResponse(
            {"ok": False, "error": "missing notification data"}, status=400
        )

    watchers = Watch.objects.filter(url=page)
    notification_data, _ = NotificationData.objects.get_or_create(
        text=title, title=title, type="content"
    )
    for watcher in watchers:
        # considering the possibility of multiple pages existing for the same path
        for user in watcher.users.all():
            Notification.objects.create(notification=notification_data, user=user)

    return JsonResponse({"ok": True}, status=200)


@never_cache
@require_http_methods(["POST"])
def update(request):
    # E.g.GET /api/v1/notifications/update/
    auth = request.headers.get("Authorization")
    if not auth or auth != settings.NOTIFICATIONS_ADMIN_TOKEN:
        return JsonResponse({"ok": False, "error": "not authorized"}, status=401)

    try:
        data = json.loads(request.body.decode("UTF-8"))
        if not data.get("filename"):
            raise Exception
    except Exception:
        return JsonResponse({"ok": False, "error": "bad data"}, status=400)

    try:
        changes = json.loads(
            requests.get(settings.NOTIFICATIONS_CHANGES_URL + data["filename"]).content
        )
    except Exception:
        return JsonResponse({"ok": False, "error": "bad url"}, status=400)

    try:
        process_changes(changes)
    except Exception:
        return JsonResponse(
            {"ok": False, "error": "Error while processing file"}, status=400
        )

    return JsonResponse({"ok": True}, status=200)
