import jingo
from tower import ugettext_lazy as _lazy

from sumo.parser import get_object_fallback
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
