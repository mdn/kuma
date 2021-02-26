from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from kuma.core.decorators import ensure_wiki_domain, shared_cache_control

from .utils import favicon_url


def home(request):
    """Home page."""
    return HttpResponse(
        """
    <html>
    End of an era. Kuma's no longer rendering a home page.<br>
    See project Yari.
    </html>
    """,
        content_type="text/html",
    )


@ensure_wiki_domain
@never_cache
def maintenance_mode(request):
    if settings.MAINTENANCE_MODE:
        return render(request, "landing/maintenance-mode.html")
    else:
        return redirect("home")


ROBOTS_ALL_ALLOWED_TXT = """\
User-agent: *
Sitemap: https://wiki.developer.mozilla.org/sitemap.xml

Disallow:
"""

ROBOTS_ALLOWED_TXT = """\
User-agent: *
Sitemap: https://developer.mozilla.org/sitemap.xml

Disallow: /api/
Disallow: /*docs/get-documents
Disallow: /*docs/Experiment:*
Disallow: /*$children
Disallow: /*docs.json
Disallow: /*/files/
Disallow: /media
Disallow: /*profiles*/edit
""" + "\n".join(
    "Disallow: /{locale}/search".format(locale=locale)
    for locale in settings.ENABLED_LOCALES
)

ROBOTS_GO_AWAY_TXT = """\
User-Agent: *
Disallow: /
"""


@shared_cache_control
def robots_txt(request):
    """Serve robots.txt that allows or forbids robots."""
    host = request.get_host()
    if host in settings.ALLOW_ROBOTS_DOMAINS:
        robots = ""
    elif host in settings.ALLOW_ROBOTS_WEB_DOMAINS:
        if host == settings.WIKI_HOST:
            robots = ROBOTS_ALL_ALLOWED_TXT
        else:
            robots = ROBOTS_ALLOWED_TXT
    else:
        robots = ROBOTS_GO_AWAY_TXT
    return HttpResponse(robots, content_type="text/plain")


class FaviconRedirect(RedirectView):
    """Redirect to the favicon in the static img folder (bug 1402497)"""

    def get_redirect_url(self, *args, **kwargs):
        return favicon_url()
