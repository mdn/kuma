from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import static
from django.views.generic import RedirectView
from ratelimit.decorators import ratelimit

from kuma.core.sections import SECTION_USAGE
from kuma.core.cache import memcache
from kuma.core.utils import is_untrusted
from kuma.feeder.models import Bundle
from kuma.search.models import Filter


def contribute_json(request):
    return static.serve(request, 'contribute.json',
                        document_root=settings.ROOT)


@ratelimit(key='user_or_ip', rate='400/m', block=True)
def home(request):
    """Home page."""
    updates = []
    for s in SECTION_USAGE:
        updates += Bundle.objects.recent_entries(s.updates)[:5]

    community_stats = memcache.get('community_stats')

    if not community_stats:
        community_stats = {'contributors': 5453, 'locales': 36}

    default_filters = Filter.objects.default_filters()

    context = {
        'updates': updates,
        'stats': community_stats,
        'default_filters': default_filters,
    }
    return render(request, 'landing/homepage.html', context)


def maintenance_mode(request):
    if settings.MAINTENANCE_MODE:
        return render(request, 'landing/maintenance-mode.html')
    else:
        return redirect('home')


def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return render(request, 'landing/promote_buttons.html')


ROBOTS_ALLOWED_TXT = '''\
User-agent: *
Sitemap: https://developer.mozilla.org/sitemap.xml

Disallow: /admin/
Disallow: /*/dashboards/*
Disallow: /*docs/feeds
Disallow: /*docs/templates
Disallow: /*docs*Template:
Disallow: /*docs/all
Disallow: /*docs/tag*
Disallow: /*docs/needs-review*
Disallow: /*docs/localization-tag*
Disallow: /*docs/with-errors
Disallow: /*docs/without-parent
Disallow: /*docs/top-level
Disallow: /*docs/new
Disallow: /*docs/get-documents
Disallow: /*docs/submit_akismet_spam
Disallow: /*docs/load*
Disallow: /*docs/Experiment:*
Disallow: /*$api
Disallow: /*$compare
Disallow: /*$revision
Disallow: /*$history
Disallow: /*$edit
Disallow: /*$children
Disallow: /*$flag
Disallow: /*$translate
Disallow: /*$locales
Disallow: /*$json
Disallow: /*$styles
Disallow: /*$toc
Disallow: /*$move
Disallow: /*$quick-review
Disallow: /*$samples
Disallow: /*$revert
Disallow: /*$repair_breadcrumbs
Disallow: /*$delete
Disallow: /*$restore
Disallow: /*$purge
Disallow: /*$subscribe
Disallow: /*$subscribe_to_tree
Disallow: /*$vote
Disallow: /*docs.json
Disallow: /*docs/ckeditor_config.js
Disallow: /*/files/
Disallow: /media
Disallow: /*move-requested
Disallow: /*preview-wiki-content
Disallow: /*profiles*/edit
Disallow: /skins
Disallow: /*type=feed
Disallow: /*users/
'''

ROBOTS_GO_AWAY_TXT = '''\
User-Agent: *
Disallow: /
'''


def robots_txt(request):
    """
    Serve robots.txt that allows or forbids robots.

    TODO: After AWS move, try different strategy (WhiteNoise, template)
    """
    if settings.ENABLE_RESTRICTIONS_BY_HOST and is_untrusted(request):
        robots = ROBOTS_GO_AWAY_TXT
    elif settings.ALLOW_ROBOTS:
        robots = ROBOTS_ALLOWED_TXT
    else:
        robots = ROBOTS_GO_AWAY_TXT
    return HttpResponse(robots, content_type='text/plain')


class FaviconRedirect(RedirectView):
    """Redirect to the favicon in the static img folder (bug 1402497)"""
    icon = None
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        assert self.icon
        return staticfiles_storage.url('img/%s' % self.icon)
