import json
import logging

from functools import partial

from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils.datastructures import SortedDict
from django.views.decorators.http import require_GET

import jingo
from tower import ugettext_lazy as _lazy, ugettext as _
from waffle.decorators import waffle_flag

from dashboards.readouts import (overview_rows, READOUTS, L10N_READOUTS,
                                 CONTRIBUTOR_READOUTS)
from sumo_locales import LOCALES
from sumo.parser import get_object_fallback
from sumo.urlresolvers import reverse
from sumo.utils import smart_int
from wiki.events import (ApproveRevisionInLocaleEvent,
                         ReviewableRevisionInLocaleEvent)
from wiki.models import Document, Revision
from wiki.views import SHOWFOR_DATA


HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore'}
MOBILE_DOCS = {'quick': 'Mobile home - Quick',
               'explore': 'Mobile home - Explore'}
PAGE_SIZE = 100


def home(request):
    data = {}
    for side, title in HOME_DOCS.iteritems():
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/home.html', data)


def mobile(request):
    data = {}
    for side, title in MOBILE_DOCS.iteritems():
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/mobile.html', data)


def _kb_readout(request, readout_slug, readouts, locale=None, mode=None):
    """Instantiate and return the readout with the given slug.

    Raise Http404 if there is no such readout.

    """
    if readout_slug not in readouts:
        raise Http404
    return readouts[readout_slug](request, locale=locale, mode=mode)


def _kb_detail(request, readout_slug, readouts, main_view_name,
               main_dash_title, locale=None):
    """Show all the rows for the given KB article statistics table."""
    return jingo.render(request, 'dashboards/kb_detail.html',
        {'readout': _kb_readout(request, readout_slug, readouts, locale),
         'locale': locale,
         'main_dash_view': main_view_name,
         'main_dash_title': main_dash_title})


@require_GET
def contributors_detail(request, readout_slug):
    """Show all the rows for the given contributor dashboard table."""
    return _kb_detail(request, readout_slug, CONTRIBUTOR_READOUTS,
                      'dashboards.contributors', _('Contributor Dashboard'),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
def localization_detail(request, readout_slug):
    """Show all the rows for the given localizer dashboard table."""
    return _kb_detail(request, readout_slug, L10N_READOUTS,
                      'dashboards.localization', _('Localization Dashboard'))


def _kb_main(request, readouts, template, locale=None, extra_data=None):
    """Render a KB statistics overview page.

    Use the given template, pass the template the given readouts, limit the
    considered data to the given locale, and pass along anything in the
    `extra_data` dict to the template in addition to the standard data.

    """
    data = {'readouts': SortedDict((slug, class_(request, locale=locale))
                         for slug, class_ in readouts.iteritems()),
            'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
            'default_locale_name':
                LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
            'current_locale_name': LOCALES[request.locale].native,
            'is_watching_approved': ApproveRevisionInLocaleEvent.is_notifying(
                request.user, locale=request.locale),
            'is_watching_locale': ReviewableRevisionInLocaleEvent.is_notifying(
                request.user, locale=request.locale),
            'is_watching_approved_default':
                ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE)}
    if extra_data:
        data.update(extra_data)
    return jingo.render(request, 'dashboards/' + template, data)


@require_GET
def localization(request):
    """Render aggregate data about articles in a non-default locale."""
    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))
    data = {'overview_rows': partial(overview_rows, request.locale)}
    return _kb_main(request, L10N_READOUTS, 'localization.html',
                    extra_data=data)


@require_GET
def contributors(request):
    """Render aggregate data about the articles in the default locale."""
    return _kb_main(request, CONTRIBUTOR_READOUTS, 'contributors.html',
                    locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
@waffle_flag('revisions_dashboard')
def revisions(request):
    """Dashboard for reviewing revisions"""
    if request.is_ajax():
        username = request.GET.get('user', None)
        locale = request.GET.get('locale', None)

        display_start = int(request.GET.get('iDisplayStart', 0))

        revisions = (Revision.objects.select_related('creator').all()
                     .order_by('-created'))
        # apply filters, limits, and pages
        if username:
            revisions = (revisions
                         .filter(creator__username__startswith=username))
        if locale:
            revisions = revisions.filter(document__locale=locale)

        total = revisions.count()
        revisions = revisions[display_start:display_start + PAGE_SIZE]

        context = {'revisions': revisions,
                   'total_records': total}
        return jingo.render(request, 'dashboards/revisions.json',
                            context, mimetype="json")
    return jingo.render(request, 'dashboards/revisions.html')


@require_GET
@waffle_flag('revisions_dashboard')
def user_lookup(request):
    """Returns partial username matches"""
    if request.is_ajax():
        user = request.GET.get('user', '')
        matches = User.objects.filter(username__startswith=user)

        userlist = []
        for u in matches:
            userlist.append({'label': u.username})

        data = json.dumps(userlist)
        return HttpResponse(data, mimetype='application/json')


@require_GET
def wiki_rows(request, readout_slug):
    """Return the table contents HTML for the given readout and mode."""
    readout = _kb_readout(request, readout_slug, READOUTS,
                          locale=request.GET.get('locale'),
                          mode=smart_int(request.GET.get('mode'), None))
    max_rows = smart_int(request.GET.get('max'), fallback=None)
    return HttpResponse(readout.render(max_rows=max_rows))
