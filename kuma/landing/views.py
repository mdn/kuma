from __future__ import unicode_literals

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import static
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from kuma.core.decorators import (beta_shared_cache_control,
                                  ensure_wiki_domain,
                                  shared_cache_control)
from kuma.core.utils import is_wiki
from kuma.feeder.models import Bundle
from kuma.feeder.sections import SECTION_HACKS
from kuma.search.models import Filter

from .utils import favicon_url


def contribute_json(request):
    cache_control = (shared_cache_control
                     if is_wiki(request) else
                     beta_shared_cache_control)
    return cache_control(static.serve)(
        request, 'contribute.json', document_root=settings.ROOT)


def home(request):
    """Home page."""
    if is_wiki(request):
        return shared_cache_control(render_home)(
            request, 'landing/homepage.html')
    return beta_shared_cache_control(render_home)(
        request, 'landing/react_homepage.html')


def render_home(request, template_name):
    """Render the home page with the template named "template_name"."""
    updates = list(Bundle.objects.recent_entries(SECTION_HACKS.updates)[:5])
    default_filters = Filter.objects.default_filters()
    context = {
        'updates': updates,
        'default_filters': default_filters,
    }
    return render(request, template_name, context)


@ensure_wiki_domain
@never_cache
def maintenance_mode(request):
    if settings.MAINTENANCE_MODE:
        return render(request, 'landing/maintenance-mode.html')
    else:
        return redirect('home')


@ensure_wiki_domain
@shared_cache_control
def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return render(request, 'landing/promote_buttons.html')


ROBOTS_ALLOWED_TXT = '''\
User-agent: *
Sitemap: https://developer.mozilla.org/sitemap.xml

Disallow: /admin/
Disallow: /api/
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
Disallow: /*$children
Disallow: /*$flag
Disallow: /*$locales
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
''' + '\n'.join('Disallow: /{locale}/search'.format(locale=locale)
                for locale in settings.ENABLED_LOCALES)

ROBOTS_GO_AWAY_TXT = '''\
User-Agent: *
Disallow: /
'''


def robots_txt(request):
    """Serve robots.txt that allows or forbids robots."""
    cache_control = (shared_cache_control
                     if is_wiki(request) else
                     beta_shared_cache_control)
    return cache_control(serve_robots_txt)(request)


def serve_robots_txt(request):
    """Select and serve the robots.txt response."""
    host = request.get_host()
    if host in settings.ALLOW_ROBOTS_DOMAINS:
        robots = ""
    elif host in settings.ALLOW_ROBOTS_WEB_DOMAINS:
        robots = ROBOTS_ALLOWED_TXT
    else:
        robots = ROBOTS_GO_AWAY_TXT
    return HttpResponse(robots, content_type='text/plain')


class FaviconRedirect(RedirectView):
    """Redirect to the favicon in the static img folder (bug 1402497)"""

    def get_redirect_url(self, *args, **kwargs):
        return favicon_url()
