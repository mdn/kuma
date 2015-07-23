import datetime
import functools
import hashlib
import random

from babel import localedata
import jinja2

from django.conf import settings

from django.utils.timezone import get_default_timezone

import jingo
from jingo import register
from tower import ungettext, ugettext as _
from taggit.models import TaggedItem

from kuma.core.cache import memcache
from kuma.core.urlresolvers import reverse
from .models import Submission
from . import DEMOS_CACHE_NS_KEY, TAG_DESCRIPTIONS, DEMO_LICENSES


TEMPLATE_INCLUDE_CACHE_EXPIRES = getattr(settings,
                                         'TEMPLATE_INCLUDE_CACHE_EXPIRES', 300)


def new_context(context, **kw):
    c = dict(context.items())
    c.update(kw)
    return c


# TODO:liberate ?
def register_cached_inclusion_tag(template, key_fn=None,
                                  expires=TEMPLATE_INCLUDE_CACHE_EXPIRES):
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

            out = memcache.get(cache_key)
            if out is None:
                context = f(*args, **kw)
                t = jingo.env.get_template(template).render(context)
                out = jinja2.Markup(t)
                memcache.set(cache_key, out, expires)
            return out

        return register.function(wrapper)
    return decorator


def submission_key(prefix):
    """Produce a cache key function with a prefix, which generates the rest of
    the key based on a submission ID and last-modified timestamp."""
    def k(*args, **kw):
        submission = args[0]
        return 'submission:%s:%s:%s' % (prefix,
                                        submission.id,
                                        submission.modified)
    return k


# TOOO: All of these inclusion tags could probably be generated & registered
# from a dict of function names and inclusion tag args, since the method bodies
# are all identical. Might be astronaut architecture, though.
@register.inclusion_tag('demos/elements/demos_head.html')
def demos_head(request):
    return locals()


@register.inclusion_tag('demos/elements/submission_creator.html')
def submission_creator(submission):
    return locals()


@register.inclusion_tag('demos/elements/user_link.html')
def user_link(user, show_gravatar=False, gravatar_size=48,
              gravatar_default='mm'):
    return locals()


@register.inclusion_tag('demos/elements/submission_thumb.html')
def submission_thumb(submission, extra_class=None, thumb_width="200",
                     thumb_height="150", is_homepage=False):
    vars = locals()

    flags = submission.get_flags()

    # Dict of metadata associated with flags for demos
    # TODO: Move to a constant or DB table? Too much view stuff here?
    flags_meta = {
        # flag name      thumb class     flag description
        'firstplace': ('first-place', _('First Place')),
        'secondplace': ('second-place', _('Second Place')),
        'thirdplace': ('third-place', _('Third Place')),
        'finalist': ('finalist', _('Finalist')),
        'featured': ('featured', _('Featured')),
    }

    # If there are any flags, pass them onto the template. Special treatment
    # for the first flag, which takes priority over all others for display in
    # the thumb.
    main_flag = (len(flags) > 0) and flags[0] or None
    vars['all_flags'] = flags
    vars['main_flag'] = main_flag
    if main_flag in flags_meta:
        vars['main_flag_class'] = flags_meta[main_flag][0]
        vars['main_flag_description'] = flags_meta[main_flag][1]
    vars['is_homepage'] = is_homepage

    return vars


def submission_listing_cache_key(*args, **kw):
    ns_key = memcache.get(DEMOS_CACHE_NS_KEY)
    if ns_key is None:
        ns_key = random.randint(1, 10000)
        memcache.set(DEMOS_CACHE_NS_KEY, ns_key)
    full_path = args[0].get_full_path()
    username = args[0].user.username
    return 'demos_%s:%s' % (
        ns_key,
        hashlib.md5(full_path + username).hexdigest())


@register_cached_inclusion_tag('demos/elements/submission_listing.html',
                               submission_listing_cache_key)
def submission_listing(request, submission_list, is_paginated, paginator,
                       page_obj, feed_title, feed_url,
                       cols_per_row=3, pagination_base_url='', show_sorts=True,
                       show_submit=False):
    return locals()


@register.inclusion_tag('demos/elements/tech_tags_list.html')
def tech_tags_list():
    return locals()


# Not cached, because it's small and changes based on
# current search query string
@register.inclusion_tag('demos/elements/search_form.html')
@jinja2.contextfunction
def search_form(context):
    return new_context(**locals())


@register.function
def devderby_tag_to_date_url(tag):
    """Turn a devderby tag like challenge:2011:june into a date-based URL"""
    # HACK: Not super happy with this, but it works for now
    if not tag:
        return ''
    parts = tag.split(':')
    return reverse('demos_devderby_by_date', args=(parts[-2], parts[-1]))


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
    if not tag:
        return ''
    name = (isinstance(tag, basestring)) and tag or tag.name
    if name in TAG_DESCRIPTIONS:
        return TAG_DESCRIPTIONS[name]['title']
    else:
        return name


@register.function
def tag_description(tag):
    if not tag:
        return ''
    name = (isinstance(tag, basestring)) and tag or tag.name
    if name in TAG_DESCRIPTIONS and 'description' in TAG_DESCRIPTIONS[name]:
        return TAG_DESCRIPTIONS[name]['description']
    else:
        return name


@register.function
def tag_learn_more(tag):
    if not tag:
        return ''
    if (tag.name in TAG_DESCRIPTIONS and
            'learn_more' in TAG_DESCRIPTIONS[tag.name]):
        return TAG_DESCRIPTIONS[tag.name]['learn_more']
    else:
        return []


@register.function
def tag_meta(tag, other_name):
    """Get metadata for a tag or tag name."""
    # TODO: Replace usage of tag_{title,description,learn_more}?
    if not tag:
        return ''
    name = (isinstance(tag, basestring)) and tag or tag.name
    if name in TAG_DESCRIPTIONS and other_name in TAG_DESCRIPTIONS[name]:
        return TAG_DESCRIPTIONS[name][other_name]
    else:
        return ''


@register.function
def tags_for_object(obj):
    tags = obj.taggit_tags.all()
    return tags


@register.function
def tech_tags_for_object(obj):
    return obj.taggit_tags.all_ns('tech')


@register.function
def tags_used_for_submissions():
    return TaggedItem.tags_for(Submission)


@register.filter
def date_diff(timestamp, to=None):
    if not timestamp:
        return ""

    compare_with = to or datetime.date.today()
    delta = timestamp - compare_with

    if delta.days == 0:
        return u"today"
    elif delta.days == -1:
        return u"yesterday"
    elif delta.days == 1:
        return u"tomorrow"

    chunks = (
        (365.0, lambda n: ungettext('year', 'years', n)),
        (30.0, lambda n: ungettext('month', 'months', n)),
        (7.0, lambda n: ungettext('week', 'weeks', n)),
        (1.0, lambda n: ungettext('day', 'days', n)),
    )

    for i, (chunk, name) in enumerate(chunks):
        if abs(delta.days) >= chunk:
            count = abs(round(delta.days / chunk, 0))
            break

    date_str = (_('%(number)d %(type)s') % {'number': count, 'type': name(count)})

    if delta.days > 0:
        return "in " + date_str
    else:
        return date_str + " ago"


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
