import time

import basket
from basket.base import BasketException

from django.conf import settings
from django.http import HttpResponseServerError
from django.shortcuts import render

import constance.config

from devmo import SECTION_USAGE
from feeder.models import Bundle
from demos.models import Submission

from .forms import SubscriptionForm


def home(request):
    """Home page."""
    demos = (Submission.objects.all_sorted('upandcoming').exclude(hidden=True))[:12]

    updates = []
    for s in SECTION_USAGE:
        updates += Bundle.objects.recent_entries(s.updates)[:5]

    return render(request, 'landing/homepage.html',
                  {'demos': demos, 'updates': updates,
                    'current_challenge_tag_name':
                    str(constance.config.DEMOS_DEVDERBY_CURRENT_CHALLENGE_TAG).strip()})


def apps_newsletter(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.locale, data=request.POST)
        context = {'subscription_form': form}
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
            del context['subscription_form']

    else:
        context = {'subscription_form': SubscriptionForm(request.locale)}

    return render(request, 'landing/apps_newsletter.html', context)


def learn(request):
    """Learn landing page."""
    return render(request, 'landing/learn.html')


def learn_html(request):
    """HTML landing page."""
    return render(request, 'landing/learn_html.html')


def learn_css(request):
    """CSS landing page."""
    return render(request, 'landing/learn_css.html')


def learn_javascript(request):
    """JavaScript landing page."""
    return render(request, 'landing/learn_javascript.html')


def promote_buttons(request):
    """Bug 646192: MDN affiliate buttons"""
    return render(request, 'landing/promote_buttons.html')


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
