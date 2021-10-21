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
        Notification.objects.filter(user_id=request.user.id).order_by("-created"),
        lambda notification: notification.serialize(),
    )
