from __future__ import unicode_literals

import datetime
import hashlib
import logging
import os
from itertools import islice

from babel import dates, localedata
from celery import chain, chord
from django.conf import settings
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import QueryDict
from django.shortcuts import _get_queryset, redirect
from django.utils.cache import patch_cache_control
from django.utils.encoding import force_bytes, force_text, smart_bytes
from django.utils.http import urlencode
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _
from polib import pofile
from pyquery import PyQuery as pq
from pytz import timezone
from six.moves.urllib.parse import parse_qsl, ParseResult, urlparse, urlsplit, urlunsplit
from taggit.utils import split_strip

from .exceptions import DateTimeFormatError


log = logging.getLogger('kuma.core.utils')


def to_html(pq):
    """
    Return valid HTML for the given PyQuery instance.

    It uses "method='html'" when calling the "html" method on the given
    PyQuery instance in order to prevent the improper closure of some empty
    HTML elements. For example, without "method='html'" the output of an empty
    "iframe" element would be "<iframe/>", which is illegal in HTML, instead of
    "<iframe></iframe>".
    """
    return pq.html(method='html')


def is_wiki(request):
    return request.get_host() == settings.WIKI_HOST


def redirect_to_wiki(request, permanent=True):
    request.META['HTTP_HOST'] = settings.WIKI_HOST
    return redirect(request.build_absolute_uri(), permanent=permanent)


def is_untrusted(request):
    return request.get_host() in (
        settings.ATTACHMENT_ORIGIN,
        settings.ATTACHMENT_HOST,
    )


def paginate(request, queryset, per_page=20):
    """Get a Paginator, abstracting some common paging actions."""
    paginator = Paginator(queryset, per_page)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = paginator.page(page)
    except (EmptyPage, InvalidPage):
        paginated = paginator.page(1)

    base = request.build_absolute_uri(request.path)

    items = [(k, v) for k in request.GET if k != 'page'
             for v in request.GET.getlist(k) if v]

    qsa = urlencode(items)

    paginated.url = '%s?%s' % (base, qsa)
    return paginated


def smart_int(string, fallback=0):
    """Convert a string to int, with fallback for invalid strings or types."""
    try:
        return int(float(string))
    except (ValueError, TypeError, OverflowError):
        return fallback


def strings_are_translated(strings, locale):
    # http://stackoverflow.com/a/24339946/571420
    pofile_path = os.path.join(settings.ROOT, 'locale', locale, 'LC_MESSAGES',
                               'django.po')
    try:
        po = pofile(pofile_path)
    except IOError:  # in case the file doesn't exist or couldn't be parsed
        return False
    all_strings_translated = True
    for string in strings:
        if not any(e for e in po if e.msgid == string and
                   (e.translated() and 'fuzzy' not in e.flags) and
                   not e.obsolete):
            all_strings_translated = False
    return all_strings_translated


def generate_filename_and_delete_previous(ffile, name, before_delete=None):
    """Generate a new filename for a file upload field; delete the previously
    uploaded file."""

    new_filename = ffile.field.generate_filename(ffile.instance, name)

    try:
        # HACK: Speculatively re-fetching the original object makes me feel
        # wasteful and dirty. But, I can't think of another way to get
        # to the original field's value. Should be cached, though.
        # see also - http://code.djangoproject.com/ticket/11663#comment:10
        orig_instance = ffile.instance.__class__.objects.get(
            id=ffile.instance.id
        )
        orig_field_file = getattr(orig_instance, ffile.field.name)
        orig_filename = orig_field_file.name

        if orig_filename and new_filename != orig_filename:
            if before_delete:
                before_delete(orig_field_file)
            orig_field_file.delete()
    except ffile.instance.__class__.DoesNotExist:
        pass

    return new_filename


def get_object_or_none(klass, *args, **kwargs):
    """
    A tool like Django's get_object_or_404 but returns None in case
    of a DoesNotExist exception.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def parse_tags(tagstring, sorted=True):
    """
    Parses tag input, with multiple word input being activated and
    delineated by commas and double quotes. Quotes take precedence, so
    they may contain commas.

    Returns a sorted list of unique tag names, unless sorted=False.

    Ported from Jonathan Buchanan's `django-tagging
    <http://django-tagging.googlecode.com/>`_
    """
    if not tagstring:
        return []

    tagstring = force_text(tagstring)

    # Special case - if there are no commas or double quotes in the
    # input, we don't *do* a recall... I mean, we know we only need to
    # split on spaces.
    if ',' not in tagstring and '"' not in tagstring:
        words = list(split_strip(tagstring, ' '))
        if sorted:
            words.sort()
        return words

    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there are
    # any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(tagstring)
    try:
        while True:
            c = i.next()
            if c == '"':
                if buffer:
                    to_be_split.append(''.join(buffer))
                    buffer = []
                # Find the matching quote
                open_quote = True
                c = i.next()
                while c != '"':
                    buffer.append(c)
                    c = i.next()
                if buffer:
                    word = ''.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == ',':
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed treat
        # the buffer as unquoted.
        if buffer:
            if open_quote and ',' in buffer:
                saw_loose_comma = True
            to_be_split.append(''.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = ','
        else:
            delimiter = ' '
        for chunk in to_be_split:
            words.extend(split_strip(chunk, delimiter))
    words = list(words)
    if sorted:
        words.sort()
    return words


def chunked(iterable, n):
    """Return chunks of n length of iterable.

    If ``len(iterable) % n != 0``, then the last chunk will have
    length less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :arg iterable: the iterable
    :arg n: the chunk length

    :returns: generator of chunks from the iterable
    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def chord_flow(pre_task, tasks, post_task):

    if settings.CELERY_TASK_ALWAYS_EAGER:
        # Eager mode and chords don't get along. So we serialize
        # the tasks as a workaround.
        tasks.insert(0, pre_task)
        tasks.append(post_task)
        return chain(*tasks)
    else:
        return chain(pre_task, chord(header=tasks, body=post_task))


def get_unique(content_type, object_pk, name=None, request=None,
               ip=None, user_agent=None, user=None):
    """Extract a set of unique identifiers from the request.

    This set will be made up of one of the following combinations, depending
    on what's available:

    * user, None, None, unique_MD5_hash
    * None, ip, user_agent, unique_MD5_hash
    """
    if request:
        if request.user.is_authenticated:
            user = request.user
            ip = user_agent = None
        else:
            user = None
            ip = request.META.get('REMOTE_ADDR', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    # HACK: Build a hash of the fields that should be unique, let MySQL
    # chew on that for a unique index. Note that any changes to this algo
    # will create all new unique hashes that don't match any existing ones.
    hash_text = "\n".join(text_type(x).encode('utf-8') for x in (
        content_type.pk, object_pk, name or '', ip, user_agent,
        (user and user.pk or 'None')
    ))
    unique_hash = hashlib.md5(hash_text).hexdigest()

    return (user, ip, user_agent, unique_hash)


def urlparams(url_, fragment=None, query_dict=None, **query):
    """
    Add a fragment and/or query parameters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url_ = urlparse(url_)
    fragment = fragment if fragment is not None else url_.fragment

    q = url_.query
    new_query_dict = (QueryDict(smart_bytes(q), mutable=True) if
                      q else QueryDict('', mutable=True))
    if query_dict:
        for k, l in query_dict.lists():
            new_query_dict[k] = None  # Replace, don't append.
            for v in l:
                new_query_dict.appendlist(k, v)

    for k, v in query.items():
        # Replace, don't append.
        if isinstance(v, list):
            new_query_dict.setlist(k, v)
        else:
            new_query_dict[k] = v

    query_string = urlencode([(k, v) for k, l in new_query_dict.lists() for
                              v in l if v is not None])
    new = ParseResult(url_.scheme, url_.netloc, url_.path, url_.params, query_string, fragment)
    return new.geturl()


def format_date_time(request, value, format='shortdatetime'):
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

    user = request.user
    try:
        if user.is_authenticated and user.timezone:
            user_tz = timezone(user.timezone)
            tzvalue = user_tz.normalize(tzvalue.astimezone(user_tz))
    except AttributeError:
        pass

    locale = _get_request_locale(request)

    try:
        formatted = format_date_value(value, tzvalue, locale, format)
    except KeyError:
        # Babel sometimes stumbles over missing formatters in some locales
        # e.g. bug #1247086
        # we fall back formatting the value with the default language code
        formatted = format_date_value(
            value, tzvalue, language_to_locale(settings.LANGUAGE_CODE), format)

    return formatted, tzvalue


def _get_request_locale(request):
    """Return locale from the request, falling back to a default if invalid."""
    locale = request.LANGUAGE_CODE
    if not localedata.exists(locale):
        locale = settings.LANGUAGE_CODE
    return language_to_locale(locale)


def format_date_value(value, tzvalue, locale, format):
    if format == 'shortdatetime':
        # Check if the date is today
        if value.toordinal() == datetime.date.today().toordinal():
            formatted = dates.format_time(tzvalue, format='short',
                                          locale=locale)
            return _('Today at %s') % formatted
        else:
            return dates.format_datetime(tzvalue, format='short',
                                         locale=locale)
    elif format == 'longdatetime':
        return dates.format_datetime(tzvalue, format='long', locale=locale)
    elif format == 'date':
        return dates.format_date(tzvalue, locale=locale)
    elif format == 'time':
        return dates.format_time(tzvalue, locale=locale)
    elif format == 'datetime':
        return dates.format_datetime(tzvalue, locale=locale)
    else:
        # Unknown format
        raise DateTimeFormatError


def language_to_locale(language_code):
    """
    Convert language codes to locale names used by Babel, Django

    Kuma uses a dash for regions, like en-US, zh-CN.
    Babel and Django use underscore, like en_US, zh_CN.
    The codes are identical when there is no region, like fr, es.

    https://docs.djangoproject.com/en/1.11/topics/i18n/#definitions
    """
    return language_code.replace('-', '_')


def add_shared_cache_control(response, **kwargs):
    """
    Adds a Cache-Control header for shared caches, like CDNs, to the
    provided response.

    Default settings (which can be overridden or extended):
    - max-age=0 - Don't use browser cache without asking if still valid
    - s-maxage=CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE - Cache in the shared
      cache for the default perioid of time
    - public - Allow intermediate proxies to cache response
    """
    nocache = (response.has_header('Cache-Control') and
               ('no-cache' in response['Cache-Control'] or
                'no-store' in response['Cache-Control']))
    if nocache:
        return

    # Set the default values.
    cc_kwargs = {
        'public': True,
        'max_age': 0,
        's_maxage': settings.CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE
    }
    # Override the default values and/or add new ones.
    cc_kwargs.update(kwargs)

    patch_cache_control(response, **cc_kwargs)


def order_params(original_url):
    """Standardize order of query parameters."""
    bits = urlsplit(original_url)
    qs = parse_qsl(bits.query, keep_blank_values=True)
    qs.sort()
    new_qs = urlencode(qs)
    new_url = urlunsplit((bits.scheme, bits.netloc, bits.path, new_qs, bits.fragment))
    return new_url


def safer_pyquery(*args, **kwargs):
    """
    PyQuery is magically clumsy in how it handles its arguments. A more
    ideal and explicit constructor would be:

        >>> from pyquery import PyQuery as pq
        >>> parsed = pq(html=my_html_string)
        >>> parsed = pq(url=definitely_a_url_string)

    But instead, you're expected to use it like this:

        >>> from pyquery import PyQuery as pq
        >>> parsed = pq(my_html_string)
        >>> parsed = pq(definitely_a_url_string)

    ...and PyQuery attempts to be smart and look at that first argument
    and if it looks like a URL, it first calls `requests.get()` on it.

    This function is a thin wrapper on that constructor that prevents
    that dangerous code to ever get a chance.

    NOTE! As of May 10 2019, this risk exists the the latest release of
    PyQuery. Hopefully it will be fixed but it would a massively disruptive
    change and thus unlikely to happen any time soon.
    """

    if isinstance(args[0], unicode):
        if args[0].split('://', 1)[0] in ('http', 'https'):
            args = (' {}'.format(args[0]),) + args[1:]
    elif isinstance(args[0], str):
        # If the input is a byte string, deal with it a byte string.
        # Since this file is using __future__.unicode_literals and
        # type and quoted string automatically becomes a unicode string.
        # In this case force it all to stay as byte strings.
        if args[0].split(force_bytes('://'), 1)[0] in (force_bytes('http'), force_bytes('https')):
            args = (force_bytes(' ') + args[0],) + args[1:]

    return pq(*args, **kwargs)
