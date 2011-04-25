import jingo

from devmo import (SECTION_USAGE, SECTION_ADDONS, SECTION_APPS, SECTION_MOBILE,
                   SECTION_WEB)
from feeder.models import Bundle, Feed


def home(request):
    """Home page."""
    tweets = []
    for section in SECTION_USAGE:
        tweets += Bundle.objects.recent_entries(section.twitter)[:2]
    tweets.sort(key=lambda t: t.last_published, reverse=True)

    updates = []
    for s in SECTION_USAGE:
        updates += Bundle.objects.recent_entries(s.updates)[:1]

    return jingo.render(request, 'landing/home.html', {
        'updates': updates, 'tweets': tweets})


def addons(request):
    """Add-ons landing page."""
    extra = {
        'discussions': Feed.objects.get(
            shortname='amo-forums').entries.all()[:4],
        'comments': Feed.objects.get(
            shortname='amo-blog-comments').entries.all()[:4],
    }
    return common_landing(request, section=SECTION_ADDONS, extra=extra)


def mozilla(request):
    """Mozilla Applications landing page."""
    return common_landing(request, section=SECTION_APPS)


def search(request):
    """Google Custom Search results page."""
    query = request.GET.get('q', '');
    return jingo.render(request, 'landing/searchresults.html', {'query': query})


def mobile(request):
    """Mobile landing page."""
    return common_landing(request, section=SECTION_MOBILE)


def web(request):
    """Web landing page."""
    return common_landing(request, section=SECTION_WEB)

def learn(request):
    """Learn landing page."""
    return jingo.render(request, 'landing/learn.html')

def learn_html(request):
    """HTML landing page."""
    return jingo.render(request, 'landing/learn_html.html')

def learn_css(request):
    """CSS landing page."""
    return jingo.render(request, 'landing/learn_css.html')

def learn_javascript(request):
    """JavaScript landing page."""
    return jingo.render(request, 'landing/learn_javascript.html')

def common_landing(request, section=None, extra=None):
    """Common code for landing pages."""
    if not section:
        raise NotImplementedError

    updates = Bundle.objects.recent_entries(section.updates)[:5]
    tweets = Bundle.objects.recent_entries(section.twitter)[:8]

    data = {'updates': updates, 'tweets': tweets}
    if extra:
        data.update(extra)

    return jingo.render(request, 'landing/%s.html' % section.short, data)
