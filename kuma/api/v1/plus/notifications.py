from __future__ import annotations

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from kuma.api.v1.plus import require_subscriber, api_list, ItemGenerationData
from kuma.notifications.models import Notification


@never_cache
@require_http_methods(["GET"])
@require_subscriber
def notifications(request):
    # E.g. GET /api/v1/notifications/
    return _notification_list(request)


@api_list
def _notification_list(request) -> ItemGenerationData:
    return (
        Notification.objects.filter(users__id=request.user.id)
        .select_related("notification")
        .order_by("-created"),
        lambda notification: notification.serialize(),
    )


@never_cache
@require_http_methods(["POST"])
@require_subscriber
def mark_as_read(request, id: int | str):
    # E.g.POST /api/v1/notifications/<id>/mark-as-read/
    kwargs = dict(users=request.user, read=False)

    if isinstance(id, int):
        kwargs["id"] = id

    unread = Notification.objects.filter(**kwargs)
    if isinstance(id, int) and not unread:
        return HttpResponseBadRequest("invalid 'id'")

    unread.update(read=True)
    return JsonResponse({"OK": True}, status=200)
