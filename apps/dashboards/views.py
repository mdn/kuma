from functools import partial

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_GET

import jingo
from tower import ugettext_lazy as _lazy

from dashboards.readouts import overview_rows, L10N_READOUTS
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
        full_title = 'Template:' + title
        data[side] = get_object_fallback(
            Document, full_title, request.locale, message, is_template=True)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/home.html', data)


def mobile(request):
    data = {}
    for side, title in MOBILE_DOCS.iteritems():
        message = _lazy('The template "%s" does not exist.') % title
        full_title = 'Template:' + title
        data[side] = get_object_fallback(
            Document, full_title, request.locale, message, is_template=True)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/mobile.html', data)


@require_GET
def localization(request):
    """Render localizer dashboard."""
    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))

    return jingo.render(request, 'dashboards/localization.html',
        {'overview_rows': partial(overview_rows, request.locale),
         'readouts': dict((slug, class_(request)) for
                          slug, class_ in L10N_READOUTS.iteritems()),
         'default_locale_name': LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
         'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
         'current_locale_name': LOCALES[request.locale].native,
        })


@require_GET
def localization_detail(request, readout):
    """Show all the rows for the given localizer dashboard table."""
    if readout not in L10N_READOUTS:
        raise Http404

    return jingo.render(request, 'dashboards/localization_detail.html',
        {'readout': L10N_READOUTS[readout](request)})


@require_GET
def contributors(request):
    return HttpResponse('<html><head><title>Hello</title></head>'
                        '<body>World</body></html>')
