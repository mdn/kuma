from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from kuma.core.decorators import shared_cache_control

from .i18n import get_kuma_languages


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
            secure=settings.LANGUAGE_COOKIE_SECURE,
        )

    return response


@shared_cache_control(s_maxage=60 * 60 * 24 * 30)
def humans_txt(request):
    """We no longer maintain an actual /humans.txt endpoint but to avoid the
    sad 404 we instead now just encourage people to go and use the GitHub
    UI to see the contributors."""
    return HttpResponse("See https://github.com/mdn/kuma/graphs/contributors\n")
