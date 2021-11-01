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
        Notification.objects.filter(users__id=request.user.id).order_by("-created"),
        lambda notification: notification.serialize(),
    )


@never_cache
@require_http_methods(["POST"])
@require_subscriber
def mark_as_read(request, id):
    # E.g.POST /api/v1/notifications/<id>/mark-as-read/
    try:
        notification = Notification.objects.get(id=id)
    except Notification.DoesNotExist:
        return HttpResponseBadRequest("invalid 'id'")

    notification.read = True
    notification.save()

    return JsonResponse({"OK": True}, status=201)
