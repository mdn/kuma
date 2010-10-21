from functools import partial

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_GET

import jingo
from tower import ugettext_lazy as _lazy

from dashboards.readouts import overview_rows, UntranslatedReadout
from sumo_locales import LOCALES
from sumo.parser import get_object_fallback
from sumo.urlresolvers import reverse
from wiki.models import Document
from wiki.views import SHOWFOR_DATA

HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore'}


def home(request):
    data = {}
    for side, title in HOME_DOCS.iteritems():
        message = _lazy('The template "%s" does not exist.') % title
        full_title = 'Template:' + title
        data[side] = get_object_fallback(
            Document, full_title, request.locale, message, is_template=True)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, 'dashboards/home.html', data)


@require_GET
def localization(request):
    """Render localizer dashboard."""
    if request.locale == settings.WIKI_DEFAULT_LANGUAGE:
        return HttpResponseRedirect(reverse('dashboards.contributors'))

    return jingo.render(request, 'dashboards/localization.html',
        {'overview_rows': partial(overview_rows, request.locale),
         'readouts':
             {'untranslated': UntranslatedReadout(request)},
         'default_locale_name': LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
         'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
         'current_locale_name': LOCALES[request.locale].native,
        })


# Tables that have their own whole-page views
READOUTS_WITH_DETAILS = dict((t.slug, t) for t in [UntranslatedReadout])


@require_GET
def localization_detail(request, readout):
    """Show all the rows for the given localizer dashboard table."""
    if readout not in READOUTS_WITH_DETAILS:
        raise Http404

    return jingo.render(request, 'dashboards/localization_detail.html',
        {'readout': READOUTS_WITH_DETAILS[readout](request)})


def contributors(request):
    return HttpResponse('<html><head><title>Hello</title></head>'
                        '<body>World</body></html>')
