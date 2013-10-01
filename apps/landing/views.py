import time
import json

import basket
from basket.base import BasketException

from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render

import constance.config
from waffle import flag_is_active
from waffle.decorators import waffle_switch
from waffle.models import Flag
from users.models import User

from devmo import (SECTION_USAGE, SECTION_ADDONS, SECTION_APPS, SECTION_MOBILE,
                   SECTION_WEB, SECTION_MOZILLA, SECTION_HACKS)
from feeder.models import Bundle, Feed
from demos.models import Submission
from landing.forms import SubscriptionForm

def home(request):
    """Home page."""

    if flag_is_active(request, 'redesign'):
        demos = Submission.objects.exclude(hidden=True).order_by('-modified').all()[:4]
    else:
        demos = Submission.objects.filter(id=constance.config.DEMOS_DEVDERBY_HOMEPAGE_FEATURED_DEMO)\
                    .exclude(hidden=True)\
                    .order_by('-modified').all()[:1]

    updates = []
    for s in SECTION_USAGE:
        updates += Bundle.objects.recent_entries(s.updates)[:5]

    return render(request, 'landing/homepage.html',
                  {'demos': demos, 'updates': updates,
                    'current_challenge_tag_name': 
                    str(constance.config.DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG).strip()})


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
    return render(request, 'landing/searchresults.html',
                  {'query': query})


def mobile(request):
    """Mobile landing page."""
    return common_landing(request, section=SECTION_MOBILE)


def hacks(request):
    """Hacks landing page."""
    return common_landing(request, section=SECTION_HACKS)


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

    return render(request, 'landing/apps_newsletter.html', context)


def learn(request):
    """Learn landing page."""
    return render(request, 'landing/learn.html')


def learn_html(request):
    """HTML landing page."""
    return render(request, 'landing/learn_html.html')


@waffle_switch('html5_landing')
def learn_html5(request):
    """HTML5 landing page."""
    demos = (Submission.objects.all_sorted()
             .filter(featured=True, taggit_tags__name__in=['tech:html5']))[:6]
    return render(request, 'landing/learn_html5.html', {'demos': demos})


def learn_css(request):
    """CSS landing page."""
    return render(request, 'landing/learn_css.html')


def learn_javascript(request):
    """JavaScript landing page."""
    return render(request, 'landing/learn_javascript.html')


def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return render(request, 'landing/promote_buttons.html')


def forum_archive(request):
    """Forum Archive from phpbb-static landing page."""
    return render(request, 'landing/forum_archive.html')

def waffles(request):
    flags = Flag.objects.all()

    flag_json = []
    for flag in flags:
        if flag_is_active(request, flag.name):
            flag_json.append({
                'name': str(flag.name),
                'note': str(flag.note)
            })

    context = { 'flags': flag_json }
    return render(request, 'landing/waffles.js', context,
                       content_type='application/x-javascript')

def common_landing(request, section=None, extra=None):
    """Common code for landing pages."""
    if not section:
        raise NotImplementedError

    updates = Bundle.objects.recent_entries(section.updates)[:5]
    tweets = Bundle.objects.recent_entries(section.twitter)[:8]

    data = {'updates': updates, 'tweets': tweets}
    if extra:
        data.update(extra)

    return render(request, 'landing/%s.html' % section.short, data)
