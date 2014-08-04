import datetime
import re
import urllib
from urlobject import URLObject
import os

from django.conf import settings
from django.core.cache import cache
from django.template import defaultfilters
from django.utils.encoding import force_text
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.contrib.messages.storage.base import LEVEL_TAGS

import bleach
from jingo import register
import jinja2
import pytz
from soapbox.models import Message
from statici18n.utils import get_filename
from django.contrib.staticfiles.storage import staticfiles_storage

from sumo.urlresolvers import split_path, reverse
from wiki.models import Document

from .utils import entity_decode


# Yanking filters from Django.
register.filter(strip_tags)
register.filter(defaultfilters.timesince)
register.filter(defaultfilters.truncatewords)
register.filter(entity_decode)


@register.function
def inlinei18n(locale):
    key = 'statici18n:%s' % locale
    path = cache.get(key)
    if path is None:
        path = os.path.join(settings.STATICI18N_OUTPUT_DIR,
                            get_filename(locale, settings.STATICI18N_DOMAIN))
        cache.set(key, path, 60 * 60 * 24 * 30)
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


@register.filter
def datetimeformat(value,
                   out_format='%Y-%m-%d',
                   in_format='%Y-%m-%dT%H:%M:%S'):
    if isinstance(value, unicode):
        try:
            value = datetime.datetime.strptime(value, in_format)
        except:
            pass
    return value.strftime(out_format)


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


# TODO: move this to wiki/helpers.py
@register.function
@jinja2.contextfunction
def devmo_url(context, path):
    """ Create a URL pointing to devmo.
        Look for a wiki page in the current locale, or default to given path
    """
    if hasattr(context['request'], 'locale'):
        locale = context['request'].locale
    else:
        locale = settings.WIKI_DEFAULT_LANGUAGE
    try:
        url = cache.get('devmo_url:%s_%s' % (locale, path))
    except:
        return path
    if not url:
        url = reverse('wiki.document',
                      locale=settings.WIKI_DEFAULT_LANGUAGE,
                      args=[path])
        if locale != settings.WIKI_DEFAULT_LANGUAGE:
            try:
                parent = Document.objects.get(
                    locale=settings.WIKI_DEFAULT_LANGUAGE, slug=path)
                """ # TODO: redirect_document is coupled to doc view
                follow redirects vs. update devmo_url calls

                target = parent.redirect_document()
                if target:
                parent = target
                """
                child = Document.objects.get(locale=locale,
                                             parent=parent)
                url = reverse('wiki.document', locale=locale,
                              args=[child.slug])
            except Document.DoesNotExist:
                pass
        cache.set('devmo_url:%s_%s' % (locale, path), url)
    return url


def get_localized_devmo_path(path, locale):
    m = get_locale_path_match(path)
    devmo_url_dict = m.groupdict()
    devmo_locale, devmo_path = devmo_url_dict['locale'], devmo_url_dict['path']
    devmo_local_path = ('/' + settings.LANGUAGE_DEKI_MAP.get(locale, 'en')
                      + '/' + devmo_path)
    return devmo_locale, devmo_path, devmo_local_path


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


@register.function
def add_utm(url_, campaign, source='developer.mozilla.org', medium='email'):
    """Add the utm_* tracking parameters to a URL."""
    url_obj = URLObject(url_).add_query_params({
        'utm_campaign': campaign,
        'utm_source': source,
        'utm_medium': medium})
    return str(url_obj)
