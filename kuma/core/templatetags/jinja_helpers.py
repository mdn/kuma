import datetime
import HTMLParser
import json

import jinja2
from django.conf import settings
from django.contrib.messages.storage.base import LEVEL_TAGS
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import defaultfilters
from django.template.loader import get_template
from django.utils.encoding import force_text
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django_jinja import library
from pytz import timezone, utc
from soapbox.models import Message
from statici18n.templatetags.statici18n import statici18n
from urlobject import URLObject

from ..urlresolvers import reverse, split_path
from ..utils import urlparams, format_date_time


htmlparser = HTMLParser.HTMLParser()


# Yanking filters from Django.
library.filter(defaultfilters.escapejs)
library.filter(defaultfilters.linebreaksbr)
library.filter(strip_tags)
library.filter(defaultfilters.truncatewords)
library.global_function(statici18n)

library.filter(urlparams)


@library.filter
def paginator(pager):
    """Render list of pages."""
    return Paginator(pager).render()


@library.global_function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    locale = kwargs.pop('locale', None)
    return reverse(viewname, args=args, kwargs=kwargs, locale=locale)


class Paginator(object):

    def __init__(self, pager):
        self.pager = pager

        self.max = 10
        self.span = (self.max - 1) / 2

        self.page = pager.number
        self.num_pages = pager.paginator.num_pages
        self.count = pager.paginator.count

        pager.page_range = self.range()
        pager.dotted_upper = self.num_pages not in pager.page_range
        pager.dotted_lower = 1 not in pager.page_range

    def range(self):
        """Return a list of page numbers to show in the paginator."""
        page, total, span = self.page, self.num_pages, self.span
        if total < self.max:
            lower, upper = 0, total
        elif page < span + 1:
            lower, upper = 0, span * 2
        elif page > total - span:
            lower, upper = total - span * 2, total
        else:
            lower, upper = page - span, page + span - 1
        return range(max(lower + 1, 1), min(total, upper) + 1)

    def render(self):
        c = {'pager': self.pager, 'num_pages': self.num_pages,
             'count': self.count}
        t = get_template('includes/paginator.html').render(c)
        return jinja2.Markup(t)


@library.filter
def yesno(boolean_value):
    return jinja2.Markup(_(u'Yes') if boolean_value else _(u'No'))


@library.filter
def entity_decode(str):
    """Turn HTML entities in a string into unicode."""
    return htmlparser.unescape(str)


@library.global_function
def page_title(title):
    return u'%s | MDN' % title


@library.filter
def level_tag(message):
    return jinja2.Markup(force_text(LEVEL_TAGS.get(message.level, ''),
                                    strings_only=True))


@library.global_function
def thisyear():
    """The current year."""
    return jinja2.Markup(datetime.date.today().year)


@library.filter
def jsonencode(data):
    return jinja2.Markup(json.dumps(data))


@library.global_function
def get_soapbox_messages(url):
    _, path = split_path(url)
    return Message.objects.match(path)


@library.global_function
def get_webfont_attributes(request):
    """
    Return data attributes based on assumptions about if user has them cached
    """
    if not request:
        return ''
    assume_loaded = 'true'
    if request.META.get('HTTP_PRAGMA') == 'no-cache':
        assume_loaded = 'false'
    elif request.META.get('HTTP_CACHE_CONTROL') == 'no-cache':
        assume_loaded = 'false'
    elif request.COOKIES.get('ffo', 'false') == 'true':
        assume_loaded = 'true'
    else:
        assume_loaded = 'false'

    font_names = ['opensanslight', 'opensans']
    font_attributes = ''
    for font_name in font_names:
        font_attributes += ' data-ffo-' + font_name + '=' + assume_loaded + ''

    return font_attributes


@library.global_function
@library.render_with('core/elements/soapbox_messages.html')
def soapbox_messages(soapbox_messages):
    return {'soapbox_messages': soapbox_messages}


@library.global_function
def add_utm(url_, campaign, source='developer.mozilla.org', medium='email'):
    """Add the utm_* tracking parameters to a URL."""
    url_obj = URLObject(url_).add_query_params({
        'utm_campaign': campaign,
        'utm_source': source,
        'utm_medium': medium})
    return str(url_obj)


@library.global_function
@jinja2.contextfunction
def datetimeformat(context, value, format='shortdatetime', output='html'):
    """
    Returns date/time formatted using babel's locale settings. Uses the
    timezone from settings.py
    """

    request = context['request']
    formatted, tzvalue = format_date_time(request, value, format)
    if output == 'json':
        return formatted
    return jinja2.Markup('<time datetime="%s">%s</time>' %
                         (tzvalue.isoformat(), formatted))


@library.global_function
def static(path):
    return staticfiles_storage.url(path)


@library.filter
def in_utc(dt):
    """
    Convert a datetime to the UTC timezone.

    Assume that naive datetimes (without timezone info) are in system time.
    """
    if dt.utcoffset() is None:
        tz = timezone(settings.TIME_ZONE)
        dt = tz.localize(dt)
    return dt.astimezone(utc)
