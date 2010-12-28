from django.conf import settings
from django.http import (HttpResponsePermanentRedirect, HttpResponseRedirect,
                         HttpResponse)

import jingo

from sumo.urlresolvers import reverse


def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page."""

    return jingo.render(request, 'handlers/403.html', status=403)


def handle404(request):
    """A handler for 404s."""

    return jingo.render(request, 'handlers/404.html', status=404)


def handle500(request):
    """A 500 message that looks nicer than the normal Apache error page."""

    return jingo.render(request, 'handlers/500.html', status=500)


def redirect_to(request, url, permanent=True):
    """Like Django's redirect_to except that 'url' is passed to reverse."""
    dest = reverse(url)
    if permanent:
        return HttpResponsePermanentRedirect(dest)

    return HttpResponseRedirect(dest)


def robots(request):
    """Generate a robots.txt."""
    if not settings.ENGAGE_ROBOTS:
        template = 'Disallow: /'
    else:
        template = jingo.render(request, 'sumo/robots.html')
    return HttpResponse(template, mimetype='text/plain')
