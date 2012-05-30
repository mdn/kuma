import datetime
import re
import httplib
import urllib
import urlparse
import socket

from django.conf import settings
from django.core.cache import cache
from django.template import defaultfilters
from django.utils.html import strip_tags

import bleach
from jingo import register
import jinja2
import pytz
from soapbox.models import Message

import utils
from sumo.urlresolvers import split_path


# Yanking filters from Django.
register.filter(strip_tags)
register.filter(defaultfilters.timesince)
register.filter(defaultfilters.truncatewords)

register.filter(utils.entity_decode)


@register.function
def page_title(title):
    return u'%s | Mozilla Developer Network' % title


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
    from django.utils import simplejson
    return jinja2.Markup(simplejson.dumps(data))


@register.function
@jinja2.contextfunction
def devmo_url(context, path):
    """ Create a URL pointing to devmo.
        Look for a wiki page in the current locale first,
        then default to given path
    """
    # HACK: If DEKIWIKI_MOCK is True, just skip hitting the API. This can speed
    # up a lot of tests without adding decorators, and should never be true in
    # production.
    if getattr(settings, 'DEKIWIKI_MOCK', False):
        return path

    if not settings.DEKIWIKI_ENDPOINT:
        # If MindTouch is unavailable, skip the rest of this
        return path

    current_locale = context['request'].locale
    m = get_locale_path_match(path)
    if not m:
        return path
    devmo_locale, devmo_path, devmo_local_path = get_localized_devmo_path(
        path,
        current_locale)
    if current_locale != devmo_locale:
        http_status_code = cache.get('devmo_local_path:%s' % devmo_local_path)
        if http_status_code is None:
            http_status_code = check_devmo_local_page(devmo_local_path)
        if http_status_code == 200:
            path = devmo_local_path
    return path


def get_localized_devmo_path(path, locale):
    m = get_locale_path_match(path)
    devmo_url_dict = m.groupdict()
    devmo_locale, devmo_path = devmo_url_dict['locale'], devmo_url_dict['path']
    devmo_local_path = ('/' + settings.LANGUAGE_DEKI_MAP.get(locale, 'en')
                      + '/' + devmo_path)
    return devmo_locale, devmo_path, devmo_local_path


def check_devmo_local_page(path):
    http_status_code = None
    try:
        deki_tuple = urlparse.urlparse(settings.DEKIWIKI_ENDPOINT)
        if deki_tuple.scheme == 'https':
            conn = httplib.HTTPSConnection(deki_tuple.netloc)
        else:
            conn = httplib.HTTPConnection(deki_tuple.netloc)
        # Seems odd, but this API resource really does require a doubly-encoded
        # page name see:
        # http://mzl.la/vqzmjX
        conn.request("GET", '/@api/deki/pages/=%s' %
                     urllib.quote(urllib.quote(path[1:], ''), ''))
        resp = conn.getresponse()
        http_status_code = resp.status
        cache.set('devmo_local_path:%s' % path, http_status_code)
        conn.close()
        return http_status_code
    except socket.error:
        pass
    return http_status_code


def get_locale_path_match(path):
    locale_regexp = "/(?P<locale>\w+)/(?P<path>.*)"
    return re.match(locale_regexp, path, re.IGNORECASE)


@register.function
def get_soapbox_messages(url):
    _, path = split_path(url)
    return Message.objects.match(path)


@register.inclusion_tag('devmo/elements/soapbox_messages.html')
def soapbox_messages(soapbox_messages):
    return {'soapbox_messages': soapbox_messages}
