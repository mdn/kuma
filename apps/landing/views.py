import time

import basket
from basket.base import BasketException

from django.conf import settings
from django.http import HttpResponseServerError

import constance.config
import jingo
from waffle.decorators import waffle_switch

from devmo import (SECTION_USAGE, SECTION_ADDONS, SECTION_APPS, SECTION_MOBILE,
                   SECTION_WEB, SECTION_MOZILLA)
from feeder.models import Bundle, Feed
from demos.models import Submission
from landing.forms import SubscriptionForm


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


def apps(request):
    """Web landing page."""
    return common_landing(request, section=SECTION_APPS,
                          extra={'form': SubscriptionForm()})


def apps_newsletter(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.locale, data=request.POST)
        context = {'form': form}
        if form.is_valid():
            optin = 'N'
            if request.locale == 'en-US':
                optin = 'Y'
            for i in range(constance.config.BASKET_RETRIES):
                try:
                    result = basket.subscribe(email=form.cleaned_data['email'],
                                 newsletters=settings.BASKET_APPS_NEWSLETTER,
                                 country=form.cleaned_data['country'],
                                 format=form.cleaned_data['format'],
                                 lang=request.locale,
                                 optin=optin)
                    if result.get('status') != 'error':
                        break
                except BasketException:
                    if i == constance.config.BASKET_RETRIES:
                        return HttpResponseServerError()
                    else:
                        time.sleep(constance.config.BASKET_RETRY_WAIT * i)
            del context['form']

    else:
        context = {'form': SubscriptionForm(request.locale)}

    return jingo.render(request, 'landing/apps_newsletter.html', context)


def learn(request):
    """Learn landing page."""
    return jingo.render(request, 'landing/learn.html')


def learn_html(request):
    """HTML landing page."""
    return jingo.render(request, 'landing/learn_html.html')


@waffle_switch('html5_landing')
def learn_html5(request):
    """HTML5 landing page."""
    demos = (Submission.objects.all_sorted()
             .filter(featured=True, taggit_tags__name__in=['tech:html5']))[:6]
    return jingo.render(request, 'landing/learn_html5.html', {'demos': demos})


def learn_css(request):
    """CSS landing page."""
    return jingo.render(request, 'landing/learn_css.html')


def learn_javascript(request):
    """JavaScript landing page."""
    return jingo.render(request, 'landing/learn_javascript.html')


def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return jingo.render(request, 'landing/promote_buttons.html')


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
