from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from kuma.core.decorators import shared_cache_control

from .i18n import get_kuma_languages


@never_cache
def _error_page(request, status):
    """
    Render error pages with jinja2.

    Sometimes, an error is raised by a middleware, and the request is not
    fully populated with a user or language code. Add in good defaults.
    """
    if not hasattr(request, "user"):
        request.user = AnonymousUser()
    if not hasattr(request, "LANGUAGE_CODE"):
        request.LANGUAGE_CODE = "en-US"
    return render(request, "%d.html" % status, status=status)


@never_cache
@csrf_exempt
@require_POST
def set_language(request):
    lang_code = request.POST.get("language")
    response = HttpResponse(status=204)

    if lang_code and lang_code in get_kuma_languages():

        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME,
            value=lang_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
        )

    return response


handler403 = lambda request, exception=None: _error_page(request, 403)
handler404 = lambda request, exception=None: _error_page(request, 404)
handler500 = lambda request, exception=None: _error_page(request, 500)


@never_cache
def rate_limited(request, exception):
    """Render a rate-limited exception."""
    response = render(request, "429.html", status=429)
    response["Retry-After"] = "60"
    return response


@shared_cache_control(s_maxage=60 * 60 * 24 * 30)
def humans_txt(request):
    """We no longer maintain an actual /humans.txt endpoint but to avoid the
    sad 404 we instead now just encourage people to go and use the GitHub
    UI to see the contributors."""
    return HttpResponse("See https://github.com/mdn/kuma/graphs/contributors\n")
