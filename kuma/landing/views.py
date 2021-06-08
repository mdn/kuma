from django.conf import settings
from django.http import HttpResponse

from kuma.core.decorators import shared_cache_control


ROBOTS_ALLOWED_TXT = """\
User-agent: *
Sitemap: https://developer.mozilla.org/sitemap.xml

Disallow: /api/
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
        robots = ROBOTS_ALLOWED_TXT
    else:
        robots = ROBOTS_GO_AWAY_TXT
    return HttpResponse(robots, content_type="text/plain")
