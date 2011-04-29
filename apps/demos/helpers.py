import datetime
import urllib
import logging
import functools
import hashlib
import random

from django.core.cache import cache
#from django.utils.translation import ungettext, ugettext
from tower import ugettext_lazy as _lazy, ungettext

from django.conf import settings

import jingo
import jinja2
from jinja2 import evalcontextfilter, Markup, escape
from jingo import register, env
from tower import ugettext as _
from tower import ugettext, ungettext
from django.core import urlresolvers

from babel import localedata
from babel.dates import format_date, format_time, format_datetime
from babel.numbers import format_decimal

from pytz import timezone
from django.utils.tzinfo import LocalTimezone

from django.core.urlresolvers import reverse as django_reverse
from devmo.urlresolvers import reverse

from tagging.models import Tag, TaggedItem
from tagging.utils import LINEAR, LOGARITHMIC

from .models import Submission, TAG_DESCRIPTIONS, DEMO_LICENSES
from . import DEMOS_CACHE_NS_KEY

from threadedcomments.models import ThreadedComment, FreeThreadedComment
from threadedcomments.forms import ThreadedCommentForm, FreeThreadedCommentForm
from threadedcomments.templatetags import threadedcommentstags
import threadedcomments.views

# Monkeypatch threadedcomments URL reverse() to use devmo's
from devmo.urlresolvers import reverse
threadedcommentstags.reverse = reverse


TEMPLATE_INCLUDE_CACHE_EXPIRES = getattr(settings, 'TEMPLATE_INCLUDE_CACHE_EXPIRES', 300)


def new_context(context, **kw):
    c = dict(context.items())
    c.update(kw)
    return c

# TODO:liberate ?
def register_cached_inclusion_tag(template, key_fn=None, expires=TEMPLATE_INCLUDE_CACHE_EXPIRES):
    """Decorator for inclusion tags with output caching. 
    
    Accepts a string or function to generate a cache key based on the incoming
    parameters, along with an expiration time configurable as
    INCLUDE_CACHE_EXPIRES or an explicit parameter"""

    if key_fn is None:
        key_fn = template

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kw):

            if type(key_fn) is str:
                cache_key = key_fn
            else:
                cache_key = key_fn(*args, **kw)
            
            out = cache.get(cache_key)
            if out is None:
                context = f(*args, **kw)
                t = jingo.env.get_template(template).render(context)
                out = jinja2.Markup(t)
                cache.set(cache_key, out, expires)
            return out

        return register.function(wrapper)
    return decorator
   
def submission_key(prefix):
    """Produce a cache key function with a prefix, which generates the rest of
    the key based on a submission ID and last-modified timestamp."""
    def k(*args, **kw):
        submission = args[0]
        return 'submission:%s:%s:%s' % ( prefix, submission.id, submission.modified )
    return k

# TOOO: All of these inclusion tags could probably be generated & registered
# from a dict of function names and inclusion tag args, since the method bodies
# are all identical. Might be astronaut architecture, though.

@register.inclusion_tag('demos/elements/submission_creator.html')
def submission_creator(submission): return locals()

@register.inclusion_tag('demos/elements/profile_link.html')
def profile_link(user, show_gravatar=False, gravatar_size=48): return locals()

@register.inclusion_tag('demos/elements/submission_thumb.html')
def submission_thumb(submission,extra_class=None): return locals()

def submission_listing_cache_key(*args, **kw):
    ns_key = cache.get(DEMOS_CACHE_NS_KEY)
    if ns_key is None:
        ns_key = random.randint(1,10000)
        cache.set(DEMOS_CACHE_NS_KEY, ns_key)
    return 'demos_%s:%s' % (ns_key, hashlib.md5(args[0].get_full_path()).hexdigest())

@register_cached_inclusion_tag('demos/elements/submission_listing.html', submission_listing_cache_key)
def submission_listing(request, submission_list, is_paginated, paginator, page_obj, feed_title, feed_url): 
    return locals()

@register.inclusion_tag('demos/elements/tags_list.html')
def tags_list(): return locals()

# Not cached, because it's small and changes based on current search query string
@register.inclusion_tag('demos/elements/search_form.html')
@jinja2.contextfunction
def search_form(context):
    return new_context(**locals())

# TODO:liberate
@register.inclusion_tag('demos/elements/gravatar.html')
def gravatar(email, size=72, default=None):
    ns = {
        's': str(size),
    }
    if default: 
        ns['default'] = default
    url = "http://www.gravatar.com/avatar/%s.jpg?%s" % (
        hashlib.md5(email).hexdigest(),
        urllib.urlencode(ns)
    )
    return {'gravatar': {'url': url, 'size': size}}

@register.function
def urlencode(args):
    """URL encode a query string from a given dict"""
    return urllib.urlencode(args)

bitly_api = None
def _get_bitly_api():
    """Get an instance of the bit.ly API class"""
    global bitly_api
    if bitly_api is None:
        import bitly
        login = getattr(settings, 'BITLY_USERNAME', '')
        apikey = getattr(settings, 'BITLY_API_KEY', '')
        bitly_api = bitly.Api(login, apikey)
    return bitly_api

@register.filter
def bitly_shorten(url):
    """Attempt to shorten a given URL through bit.ly / mzl.la"""
    try:
        # TODO:caching
        return _get_bitly_api().shorten(url)
    except:
        # Just in case the bit.ly service fails or the API key isn't
        # configured, fall back to using the original URL.
        return url

@register.function
def license_link(license_name):
    if license_name in DEMO_LICENSES:
        return DEMO_LICENSES[license_name]['link']
    else:
        return license_name

@register.function
def license_title(license_name):
    if license_name in DEMO_LICENSES:
        return DEMO_LICENSES[license_name]['title']
    else:
        return license_name

@register.function
def tag_title(tag):
    if tag.name in TAG_DESCRIPTIONS:
        return TAG_DESCRIPTIONS[tag.name]['title']
    else:
        return tag.name

@register.function
def tag_description(tag):
    if tag.name in TAG_DESCRIPTIONS:
        return TAG_DESCRIPTIONS[tag.name]['description']
    else:
        return tag.name

@register.function
def tag_learn_more(tag):
    if tag.name in TAG_DESCRIPTIONS and 'learn_more' in TAG_DESCRIPTIONS[tag.name]:
        return TAG_DESCRIPTIONS[tag.name]['learn_more']
    else:
        return []

@register.function
def tags_for_object(obj):
    tags = Tag.objects.get_for_object(obj)
    return tags

@register.function
def tags_used_for_submissions():
    return Tag.objects.usage_for_model(Submission, counts=True, min_count=1)

@register.filter
def date_diff(timestamp, to=None):
    if not timestamp:
        return ""

    compare_with = to or datetime.date.today()
    delta = timestamp - compare_with
    
    if delta.days == 0: return u"today"
    elif delta.days == -1: return u"yesterday"
    elif delta.days == 1: return u"tomorrow"
    
    chunks = (
        (365.0, lambda n: ungettext('year', 'years', n)),
        (30.0, lambda n: ungettext('month', 'months', n)),
        (7.0, lambda n : ungettext('week', 'weeks', n)),
        (1.0, lambda n : ungettext('day', 'days', n)),
    )
    
    for i, (chunk, name) in enumerate(chunks):
        if abs(delta.days) >= chunk:
            count = abs(round(delta.days / chunk, 0))
            break

    date_str = ugettext('%(number)d %(type)s') % {'number': count, 'type': name(count)}
    
    if delta.days > 0: return "in " + date_str
    else: return date_str + " ago"

# TODO: Maybe just register the template tag functions in the jingo environment
# directly, rather than building adapter functions?

@register.function
def get_threaded_comment_flat(content_object, tree_root=0):
    return ThreadedComment.public.get_tree(content_object, root=tree_root)

@register.function
def get_threaded_comment_tree(content_object, tree_root=0):
    """Convert the flat list with depth indices into a true tree structure for
    recursive template display"""
    root = dict( children=[] )
    parent_stack = [ root, ]
    
    flat = ThreadedComment.public.get_tree(content_object, root=tree_root)
    for comment in flat:
        c = dict(comment=comment, children=[])
        if comment.depth > len(parent_stack) - 1 and len(parent_stack[-1]['children']):
            parent_stack.append(parent_stack[-1]['children'][-1])
        while comment.depth < len(parent_stack) - 1:
            parent_stack.pop(-1)
        parent_stack[-1]['children'].append(c)

    return root

@register.inclusion_tag('demos/elements/comments_tree.html')
def comments_tree(request, object, root): return locals()

@register.function
def get_comment_url(content_object, parent=None):
    return threadedcommentstags.get_comment_url(content_object, parent)

@register.function
def get_threaded_comment_form():
    return ThreadedCommentForm()

@register.function
def auto_transform_markup(comment):
    return threadedcommentstags.auto_transform_markup(comment)

@register.function
def can_delete_comment(comment, user):
    return threadedcomments.views.can_delete_comment(comment, user)

@register.filter
def timesince(d, now=None):
    """Take two datetime objects and return the time between d and now as a
    nicely formatted string, e.g. "10 minutes". If d is None or occurs after
    now, return ''.

    Units used are years, months, weeks, days, hours, and minutes. Seconds and
    microseconds are ignored. Just one unit is displayed. For example,
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
            now = datetime.datetime.now(LocalTimezone(d))
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

    return jinja2.Markup('<time datetime="%s">%s</time>' % \
                         (tzvalue.isoformat(), formatted))

