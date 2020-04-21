from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import static
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from kuma.core.decorators import ensure_wiki_domain, shared_cache_control
from kuma.core.utils import is_wiki
from kuma.feeder.models import Bundle
from kuma.feeder.sections import SECTION_HACKS
from kuma.search.models import Filter

from .utils import favicon_url


@shared_cache_control
def contribute_json(request):
    return static.serve(request, "contribute.json", document_root=settings.ROOT)


@shared_cache_control
def home(request):
    """Home page."""
    context = {}
    # Need for both wiki and react homepage
    context["updates"] = list(Bundle.objects.recent_entries(SECTION_HACKS.updates)[:5])

    # The default template name
    template_name = "landing/react_homepage.html"
    if is_wiki(request):
        template_name = "landing/homepage.html"
        context["default_filters"] = Filter.objects.default_filters()
    return render(request, template_name, context)


@ensure_wiki_domain
@never_cache
def maintenance_mode(request):
    if settings.MAINTENANCE_MODE:
        return render(request, "landing/maintenance-mode.html")
    else:
        return redirect("home")


@ensure_wiki_domain
@shared_cache_control
def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return render(request, "landing/promote_buttons.html")


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
Disallow: /*users/
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
