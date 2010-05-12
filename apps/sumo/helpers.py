import cgi
import urlparse
import datetime

from django.utils.encoding import smart_unicode
from django.conf import settings

import jinja2
from jingo import register, env
from tower import ugettext_lazy as _lazy
from babel import localedata
from babel.dates import format_date, format_time, format_datetime
from pytz import timezone

from sumo.urlresolvers import reverse
from sumo.utils import urlencode


class DateTimeFormatError(Exception):
    pass


@register.filter
def paginator(pager):
    return Paginator(pager).render()


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def urlparams(url_, hash=None, **query):
    """
    Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    items = []
    if url.query:
        for k, v in cgi.parse_qsl(url.query):
            items.append((k, v))
    for k, v in query.items():
        items.append((k, v))

    items = [(k, unicode(v).encode('raw_unicode_escape')) for
             k, v in items if v is not None]

    query_string = urlencode(items)

    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return jinja2.Markup(new.geturl())


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
        t = env.get_template('layout/paginator.html').render(**c)
        return jinja2.Markup(t)


@register.filter
def fe(str, *args, **kwargs):
    """Format a safe string with potentially unsafe arguments, then return a
    safe string."""

    str = unicode(str)

    args = [jinja2.escape(smart_unicode(v)) for v in args]

    for k in kwargs:
        kwargs[k] = jinja2.escape(smart_unicode(kwargs[k]))

    return jinja2.Markup(str.format(*args, **kwargs))


@register.function
@jinja2.contextfunction
def breadcrumbs(context, items=list(), add_default=True):
    """
    Show a list of breadcrumbs. If url is None, it won't be a link.
    Accepts: [(url, label)]
    """
    if add_default:
        crumbs = [('/' + context['request'].locale + '/kb',
                   _lazy('Firefox Support'))]
    else:
        crumbs = []

    # add user-defined breadcrumbs
    if items:
        try:
            crumbs += items
        except TypeError:
            crumbs.append(items)

    c = {'breadcrumbs': crumbs}
    t = env.get_template('layout/breadcrumbs.html').render(**c)
    return jinja2.Markup(t)


@register.function
def profile_url(user):
    """Return a URL to the user's profile."""
    # TODO: revisit this when we have a users app
    return '/tiki-user_information.php?locale=en-US&userId=%s' % user.id


@register.function
@jinja2.contextfunction
def datetimeformat(context, value, format='shortdatetime'):
    """
    Returns date/time formatted using babel's locale settings. Uses the
    timezone from settings.py
    """
    if not isinstance(value, datetime.datetime):
        # Expecting date value
        raise ValueError

    tzinfo = timezone(settings.TIME_ZONE)
    tzvalue = tzinfo.localize(value)
    # Babel uses underscore as separator.
    locale = context['request'].locale
    if not localedata.exists(locale):
        locale = settings.LANGUAGE_CODE
    locale = locale.replace('-', '_')

    # If within a day, 24 * 60 * 60 = 86400s
    if format == 'shortdatetime':
        # Check if the date is today
        if value.toordinal() == datetime.date.today().toordinal():
            return _lazy('Today at %s') % format_time(
                tzvalue, format='short', locale=locale)
        else:
            return format_datetime(tzvalue, format='short', locale=locale)
    elif format == 'longdatetime':
        return format_datetime(tzvalue, format='long', locale=locale)
    elif format == 'date':
        return format_date(tzvalue, locale=locale)
    elif format == 'time':
        return format_time(tzvalue, locale=locale)
    elif format == 'datetime':
        return format_datetime(tzvalue, locale=locale)
    else:
        # Unknown format
        raise DateTimeFormatError
