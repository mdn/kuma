import datetime
import HTMLParser
import os
import urllib
import hashlib
import bitly_api

from babel import localedata
from babel.dates import format_date, format_time, format_datetime
from babel.numbers import format_decimal
import bleach
import pytz
from urlobject import URLObject
from jingo import register, env
import jinja2
from pytz import timezone
from tower import ugettext_lazy as _lazy, ungettext

from django.conf import settings
from django.contrib.messages.storage.base import LEVEL_TAGS
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import defaultfilters
from django.utils.encoding import smart_str, force_text
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.timezone import get_default_timezone

from soapbox.models import Message
from statici18n.utils import get_filename

from .cache import memcache
from .exceptions import DateTimeFormatError
from .urlresolvers import reverse, split_path


htmlparser = HTMLParser.HTMLParser()


# Yanking filters from Django.
register.filter(strip_tags)
register.filter(defaultfilters.timesince)
register.filter(defaultfilters.truncatewords)


@register.filter
def paginator(pager):
    """Render list of pages."""
    return Paginator(pager).render()


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    locale = kwargs.pop('locale', None)
    return reverse(viewname, args=args, kwargs=kwargs, locale=locale)

bitly = bitly_api.Connection(login=getattr(settings, 'BITLY_USERNAME', ''),
                             api_key=getattr(settings, 'BITLY_API_KEY', ''))


@register.filter
def bitly_shorten(url):
    """Attempt to shorten a given URL through bit.ly / mzl.la"""
    cache_key = 'bitly:%s' % hashlib.md5(smart_str(url)).hexdigest()
    short_url = memcache.get(cache_key)
    if short_url is None:
        try:
            short_url = bitly.shorten(url)['url']
            memcache.set(cache_key, short_url, 60 * 60 * 24 * 30 * 12)
        except (bitly_api.BitlyError, KeyError):
            # Just in case the bit.ly service fails or the API key isn't
            # configured, fall back to using the original URL.
            return url
    return short_url


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
        t = env.get_template('includes/paginator.html').render(c)
        return jinja2.Markup(t)


@register.filter
def timesince(d, now=None):
    """Take two datetime objects and return the time between d and now as a
    nicely formatted string, e.g. "10 minutes".  If d is None or occurs after
    now, return ''.

    Units used are years, months, weeks, days, hours, and minutes. Seconds and
    microseconds are ignored.  Just one unit is displayed.  For example,
    "2 weeks" and "1 year" are possible outputs, but "2 weeks, 3 days" and "1
    year, 5 months" are not.

    Adapted from django.utils.timesince to have better i18n (not assuming
    commas as list separators and including "ago" so order of words isn't
    assumed), show only one time unit, and include seconds.

    """
    if d is None:
        return u''
    chunks = [
        (60 * 60 * 24 * 365, lambda n: ungettext('%(number)d year ago',
                                                 '%(number)d years ago', n)),
        (60 * 60 * 24 * 30, lambda n: ungettext('%(number)d month ago',
                                                '%(number)d months ago', n)),
        (60 * 60 * 24 * 7, lambda n: ungettext('%(number)d week ago',
                                               '%(number)d weeks ago', n)),
        (60 * 60 * 24, lambda n: ungettext('%(number)d day ago',
                                           '%(number)d days ago', n)),
        (60 * 60, lambda n: ungettext('%(number)d hour ago',
                                      '%(number)d hours ago', n)),
        (60, lambda n: ungettext('%(number)d minute ago',
                                 '%(number)d minutes ago', n)),
        (1, lambda n: ungettext('%(number)d second ago',
                                '%(number)d seconds ago', n))]
    if not now:
        if d.tzinfo:
            now = datetime.datetime.now(get_default_timezone())
        else:
            now = datetime.datetime.now()

    # Ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u''
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    return name(count) % {'number': count}


@register.filter
def yesno(boolean_value):
    return jinja2.Markup(_lazy(u'Yes') if boolean_value else _lazy(u'No'))


@register.filter
def entity_decode(str):
    """Turn HTML entities in a string into unicode."""
    return htmlparser.unescape(str)


@register.function
def inlinei18n(locale):
    key = 'statici18n:%s' % locale
    path = memcache.get(key)
    if path is None:
        path = os.path.join(settings.STATICI18N_OUTPUT_DIR,
                            get_filename(locale, settings.STATICI18N_DOMAIN))
        memcache.set(key, path, 60 * 60 * 24 * 30)
    with staticfiles_storage.open(path) as i18n_file:
        return mark_safe(i18n_file.read())


@register.function
def page_title(title):
    return u'%s | MDN' % title


@register.filter
def level_tag(message):
    return jinja2.Markup(force_text(LEVEL_TAGS.get(message.level, ''),
                                    strings_only=True))


@register.filter
def isotime(t):
    """Date/Time format according to ISO 8601"""
    if not hasattr(t, 'tzinfo'):
        return
    return _append_tz(t).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_tz(t):
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(t)


@register.function
def thisyear():
    """The current year."""
    return jinja2.Markup(datetime.date.today().year)


@register.filter
def cleank(txt):
    """Clean and link some user-supplied text."""
    return jinja2.Markup(bleach.linkify(bleach.clean(txt)))


@register.filter
def urlencode(txt):
    """Url encode a path."""
    return urllib.quote_plus(txt.encode('utf8'))


@register.filter
def jsonencode(data):
    import json
    return jinja2.Markup(json.dumps(data))


@register.function
def get_soapbox_messages(url):
    _, path = split_path(url)
    return Message.objects.match(path)


@register.function
def get_webfont_attributes(request):
    """Return data attributes based on assumptions about if user has them cached"""
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


@register.inclusion_tag('core/elements/soapbox_messages.html')
def soapbox_messages(soapbox_messages):
    return {'soapbox_messages': soapbox_messages}


@register.function
def add_utm(url_, campaign, source='developer.mozilla.org', medium='email'):
    """Add the utm_* tracking parameters to a URL."""
    url_obj = URLObject(url_).add_query_params({
        'utm_campaign': campaign,
        'utm_source': source,
        'utm_medium': medium})
    return str(url_obj)


def _babel_locale(locale):
    """Return the Babel locale code, given a normal one."""
    # Babel uses underscore as separator.
    return locale.replace('-', '_')


def _contextual_locale(context):
    """Return locale from the context, falling back to a default if invalid."""
    locale = context['request'].locale
    if not localedata.exists(locale):
        locale = settings.LANGUAGE_CODE
    return locale


@register.function
@jinja2.contextfunction
def datetimeformat(context, value, format='shortdatetime', output='html'):
    """
    Returns date/time formatted using babel's locale settings. Uses the
    timezone from settings.py
    """
    if not isinstance(value, datetime.datetime):
        if isinstance(value, datetime.date):
            # Turn a date into a datetime
            value = datetime.datetime.combine(value,
                                              datetime.datetime.min.time())
        else:
            # Expecting datetime value
            raise ValueError

    default_tz = timezone(settings.TIME_ZONE)
    tzvalue = default_tz.localize(value)

    user = context['request'].user
    try:
        if user.is_authenticated() and user.profile.timezone:
            user_tz = user.profile.timezone
            tzvalue = user_tz.normalize(tzvalue.astimezone(user_tz))
    except AttributeError:
        pass

    locale = _babel_locale(_contextual_locale(context))

    # If within a day, 24 * 60 * 60 = 86400s
    if format == 'shortdatetime':
        # Check if the date is today
        if value.toordinal() == datetime.date.today().toordinal():
            formatted = _lazy(u'Today at %s') % format_time(
                tzvalue, format='short', locale=locale)
        else:
            formatted = format_datetime(tzvalue, format='short', locale=locale)
    elif format == 'longdatetime':
        formatted = format_datetime(tzvalue, format='long', locale=locale)
    elif format == 'date':
        formatted = format_date(tzvalue, locale=locale)
    elif format == 'time':
        formatted = format_time(tzvalue, locale=locale)
    elif format == 'datetime':
        formatted = format_datetime(tzvalue, locale=locale)
    else:
        # Unknown format
        raise DateTimeFormatError

    if output == 'json':
        return formatted
    return jinja2.Markup('<time datetime="%s">%s</time>' %
                         (tzvalue.isoformat(), formatted))


@register.function
@jinja2.contextfunction
def number(context, n):
    """Return the localized representation of an integer or decimal.

    For None, print nothing.

    """
    if n is None:
        return ''
    return format_decimal(n, locale=_babel_locale(_contextual_locale(context)))
