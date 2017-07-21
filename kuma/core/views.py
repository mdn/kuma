from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .decorators import never_cache


def _error_page(request, status):
    """Render error pages with jinja2."""
    return render(request, '%d.html' % status, status=status)


@csrf_exempt
@require_POST
def set_language(request):
    lang_code = request.POST.get("language")
    response = HttpResponse(status=204)

    if lang_code and lang_code in dict(settings.LANGUAGES):

        response.set_cookie(key=settings.LANGUAGE_COOKIE_NAME,
                            value=lang_code,
                            max_age=settings.LANGUAGE_COOKIE_AGE,
                            path=settings.LANGUAGE_COOKIE_PATH,
                            domain=settings.LANGUAGE_COOKIE_DOMAIN,
                            )

    return response


handler403 = lambda request: _error_page(request, 403)
handler404 = lambda request: _error_page(request, 404)
handler500 = lambda request: _error_page(request, 500)


@never_cache
def rate_limited(request, exception):
    """Render a rate-limited exception."""
    response = render(request, '429.html', status=429)
    response['Retry-After'] = '60'
    return response
