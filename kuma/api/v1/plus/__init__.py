import functools
from typing import Callable, Tuple

from django.db.models import QuerySet
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token


def require_subscriber(view_function):
    @functools.wraps(view_function)
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden("not signed in")
        if not user.is_active:
            return HttpResponseForbidden("not a subscriber")
        return view_function(request, *args, **kwargs)

    return inner


ItemGenerationData = Tuple[QuerySet, Callable]


def api_list(item_generator: Callable[..., ItemGenerationData]):
    @functools.wraps(item_generator)
    def inner(request, *args, **kwargs):
        try:
            page = int(request.GET.get("page") or "1")
            assert 0 < page < 100
        except (ValueError, AssertionError):
            return HttpResponseBadRequest("invalid 'page'")

        try:
            per_page = int(request.GET.get("per_page") or settings.API_V1_PAGE_SIZE)
            assert 0 < per_page <= 100
        except (ValueError, AssertionError):
            return HttpResponseBadRequest("invalid 'per_page'")

        items, serialize = item_generator(request, *args, **kwargs)

        m = (page - 1) * per_page
        n = page * per_page
        context = {
            "items": [serialize(i) for i in items[m:n]],
            "metadata": {
                "total": items.count(),
                "page": page,
                "per_page": per_page,
            },
            "csrfmiddlewaretoken": get_token(request),
        }
        return JsonResponse(context)

    return inner
