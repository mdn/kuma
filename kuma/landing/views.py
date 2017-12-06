from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.shortcuts import redirect, render
from django.views import static
from django.views.generic import RedirectView
from ratelimit.decorators import ratelimit

from kuma.settings.common import path
from kuma.core.sections import SECTION_USAGE
from kuma.core.cache import memcache
from kuma.feeder.models import Bundle
from kuma.search.models import Filter


def contribute_json(request):
    return static.serve(request, 'contribute.json',
                        document_root=settings.ROOT)


def fellowship(request):
    return render(request, 'landing/fellowship.html')


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


def robots_txt(request):
    """
    Serve robots.txt that allows or forbids robots.

    TODO: After AWS move, try different strategy (WhiteNoise, template)
    """
    if settings.ALLOW_ROBOTS:
        robots = 'robots.txt'
    else:
        robots = 'robots-go-away.txt'
    return static.serve(request, robots, document_root=path('media'))


class FaviconRedirect(RedirectView):
    """Redirect to the favicon in the static img folder (bug 1402497)"""
    icon = None
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        assert self.icon
        return staticfiles_storage.url('img/%s' % self.icon)
