from functools import partial

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.views.decorators.http import require_GET

import jingo
from tower import ugettext_lazy as _lazy, ugettext as _

from dashboards.readouts import (overview_rows, L10N_READOUTS,
                                 CONTRIBUTOR_READOUTS)
from sumo_locales import LOCALES
from sumo.parser import get_object_fallback
from sumo.urlresolvers import reverse
from wiki.models import Document
from wiki.views import SHOWFOR_DATA


HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore'}
MOBILE_DOCS = {'quick': 'Mobile home - Quick',
               'explore': 'Mobile home - Explore'}


def home(request):
    data = {}
    for side, title in HOME_DOCS.iteritems():
        message = _lazy('The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/home.html', data)


def mobile(request):
    data = {}
    for side, title in MOBILE_DOCS.iteritems():
        message = _lazy('The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/mobile.html', data)


def _kb_detail(request, readout_slug, readouts, main_view_name,
               main_dash_title, locale=None):
    """Show all the rows for the given KB article statistics table."""
    if readout_slug not in readouts:
        raise Http404
    return jingo.render(request, 'dashboards/kb_detail.html',
        {'readout': readouts[readout_slug](request, locale),
         'main_dash_view': main_view_name,
         'main_dash_title': main_dash_title})


@require_GET
def contributors_detail(request, readout):
    """Show all the rows for the given contributor dashboard table."""
    return _kb_detail(request, readout, CONTRIBUTOR_READOUTS,
                      'dashboards.contributors', _('Contributor Dashboard'),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)


@require_GET
def localization_detail(request, readout):
    """Show all the rows for the given localizer dashboard table."""
    return _kb_detail(request, readout, L10N_READOUTS,
                      'dashboards.localization', _('Localization Dashboard'))


def _kb_main(request, readouts, template, locale=None, extra_data=None):
    """Render a KB statistics overview page.

    Use the given template, pass the template the given readouts, limit the
    considered data to the given locale, and pass along anything in the
    `extra_data` dict to the template in addition to the standard data.

    """
    data = {'readouts': SortedDict((slug, class_(request, locale=locale))
                         for slug, class_ in readouts.iteritems()),
            'default_locale_name':
                LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
            'current_locale_name': LOCALES[request.locale].native}
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
