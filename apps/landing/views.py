from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect

import jingo
from tower import ugettext as _
from waffle.decorators import waffle_switch
import basket

from devmo import (SECTION_USAGE, SECTION_ADDONS, SECTION_APPS, SECTION_MOBILE,
                   SECTION_WEB, SECTION_MOZILLA)
from feeder.models import Bundle, Feed
from demos.models import Submission
from landing.forms import SubscriptionForm
from sumo.urlresolvers import reverse


def home(request):
    """Home page."""

    demos = (Submission.objects.all_sorted('upandcoming')
            .exclude(hidden=True))[:5]

    tweets = []
    for section in SECTION_USAGE:
        tweets += Bundle.objects.recent_entries(section.twitter)[:2]
    tweets.sort(key=lambda t: t.last_published, reverse=True)

    updates = []
    for s in SECTION_USAGE:
        updates += Bundle.objects.recent_entries(s.updates)[:1]

    return jingo.render(request, 'landing/home.html', {
        'demos': demos, 'updates': updates, 'tweets': tweets})


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
    return common_landing(request, section=SECTION_MOZILLA)


def search(request):
    """Google Custom Search results page."""
    query = request.GET.get('q', '')
    return jingo.render(request, 'landing/searchresults.html',
                        {'query': query})


def mobile(request):
    """Mobile landing page."""
    return common_landing(request, section=SECTION_MOBILE)


def web(request):
    """Web landing page."""
    return common_landing(request, section=SECTION_WEB)


@waffle_switch('apps_landing')
def apps(request):
    """Web landing page."""
    return common_landing(request, section=SECTION_APPS,
                          extra={'form': SubscriptionForm()})


@waffle_switch('apps_landing')
def apps_subscription(request):
    form = SubscriptionForm(data=request.POST)
    if form.is_valid():
        optin = 'N'
        if request.locale == 'en-US':
            optin = 'Y'
        basket.subscribe(email=form.cleaned_data['email'],
                         newsletters=settings.BASKET_APPS_NEWSLETTER,
                         format=form.cleaned_data['format'],
                         lang=request.locale,
                         optin=optin)
        messages.success(request,
            _('Thank you for subscribing to the Apps Developer newsletter.'))
        return HttpResponseRedirect(reverse('apps'))

    """Web landing page."""
    return common_landing(request, section=SECTION_APPS, extra={'form': form})


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


def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return jingo.render(request, 'landing/promote_buttons.html')


def discussion(request):
    """Discussion landing page."""
    return jingo.render(request, 'landing/discussion.html')


def forum_archive(request):
    """Forum Archive from phpbb-static landing page."""
    return jingo.render(request, 'landing/forum_archive.html')


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
