from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from kuma.api.v1.plus import require_subscriber
from kuma.notifications.models import Notification


@never_cache
@require_http_methods(["GET"])
@require_subscriber
def notifications(request):
    # E.g. GET /api/v1/notifications/
    try:
        page = int(request.GET.get("page") or "1")
        assert 0 < page < 100
    except (ValueError, AssertionError):
        return HttpResponseBadRequest("invalid 'page'")

    try:
        limit = int(request.GET.get("page") or "1")
    except (ValueError):
        return HttpResponseBadRequest("invalid 'limit'")

    try:
        per_page = int(
            request.GET.get("per_page") or settings.API_V1_BOOKMARKS_PAGE_SIZE
        )
        assert 0 < per_page <= 100
    except (ValueError, AssertionError):
        return HttpResponseBadRequest("invalid 'per_page'")

    notifications = Notification.objects.filter(user_id=request.user.id).order_by(
        "-created"
    )

    def serialize(qs: QuerySet):
        for notification in qs:
            # In Yari, the `metadata["parents"]` will always include "self"
            # in the last link. Omit that here.
            yield {
                "id": notification.id,
            }

    m = (page - 1) * per_page
    n = page * per_page
    context = {
        "items": list(serialize(notifications[m:n])),
        "metadata": {
            "total": notifications.count(),
            "page": page,
            "per_page": per_page,
        },
        "csrfmiddlewaretoken": get_token(request),
    }
    return JsonResponse(context)
