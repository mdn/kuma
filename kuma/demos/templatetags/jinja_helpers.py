import datetime
import functools
import hashlib
import random

import bitly_api
import jinja2
from django.conf import settings
from django.template.loader import get_template
from django.utils.encoding import smart_str
from django.utils.translation import ugettext, ungettext
from django_jinja import library
from taggit.models import TaggedItem

from kuma.core.cache import memcache
from kuma.core.urlresolvers import reverse
from kuma.core.utils import bitly

from .. import DEMO_LICENSES, DEMOS_CACHE_NS_KEY, TAG_DESCRIPTIONS
from ..models import Submission


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
                t = get_template(template).render(context)
                out = jinja2.Markup(t)
                memcache.set(cache_key, out, expires)
            return out

        return library.global_function(wrapper)
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
@library.global_function
@library.render_with('demos/elements/demos_head.html')
def demos_head(request):
    return locals()


@library.global_function
@library.render_with('demos/elements/submission_creator.html')
def submission_creator(submission):
    return locals()


@library.global_function
@library.render_with('demos/elements/user_link.html')
def user_link(user, show_gravatar=False, gravatar_size=48,
              gravatar_default='mm'):
    return locals()


@library.global_function
@library.render_with('demos/elements/submission_thumb.html')
def submission_thumb(submission, extra_class=None, thumb_width="200",
                     thumb_height="150", is_homepage=False):
    vars = locals()

    flags = submission.get_flags()

    # Dict of metadata associated with flags for demos
    # TODO: Move to a constant or DB table? Too much view stuff here?
    flags_meta = {
        # flag name      thumb class     flag description
        'firstplace': ('first-place', ugettext('First Place')),
        'secondplace': ('second-place', ugettext('Second Place')),
        'thirdplace': ('third-place', ugettext('Third Place')),
        'finalist': ('finalist', ugettext('Finalist')),
        'featured': ('featured', ugettext('Featured')),
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


@library.global_function
@library.render_with('demos/elements/tech_tags_list.html')
def tech_tags_list():
    return locals()


# Not cached, because it's small and changes based on
# current search query string
@library.global_function
@library.render_with('demos/elements/search_form.html')
@jinja2.contextfunction
def search_form(context):
    return new_context(**locals())


@library.global_function
def devderby_tag_to_date_url(tag):
    """Turn a devderby tag like challenge:2011:june into a date-based URL"""
    # HACK: Not super happy with this, but it works for now
    if not tag:
        return ''
    parts = tag.split(':')
    return reverse('demos_devderby_by_date', args=(parts[-2], parts[-1]))


@library.global_function
def license_link(license_name):
    if license_name in DEMO_LICENSES:
        return DEMO_LICENSES[license_name]['link']
    else:
        return license_name


@library.global_function
def license_title(license_name):
    if license_name in DEMO_LICENSES:
        return DEMO_LICENSES[license_name]['title']
    else:
        return license_name


@library.global_function
def tag_title(tag):
    if not tag:
        return ''
    name = (isinstance(tag, basestring)) and tag or tag.name
    if name in TAG_DESCRIPTIONS:
        return TAG_DESCRIPTIONS[name]['title']
    else:
        return name


@library.global_function
def tag_description(tag):
    if not tag:
        return ''
    name = (isinstance(tag, basestring)) and tag or tag.name
    if name in TAG_DESCRIPTIONS and 'description' in TAG_DESCRIPTIONS[name]:
        return TAG_DESCRIPTIONS[name]['description']
    else:
        return name


@library.global_function
def tag_learn_more(tag):
    if not tag:
        return ''
    if (tag.name in TAG_DESCRIPTIONS and
            'learn_more' in TAG_DESCRIPTIONS[tag.name]):
        return TAG_DESCRIPTIONS[tag.name]['learn_more']
    else:
        return []


@library.global_function
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


@library.global_function
def tags_for_object(obj):
    tags = obj.taggit_tags.all()
    return tags


@library.global_function
def tech_tags_for_object(obj):
    return obj.taggit_tags.all_ns('tech')


@library.global_function
def tags_used_for_submissions():
    return TaggedItem.tags_for(Submission)


@library.filter
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

    date_str = ugettext('%(number)d %(type)s') % {'number': count,
                                                  'type': name(count)}

    if delta.days > 0:
        return "in " + date_str
    else:
        return date_str + " ago"


# Note: Deprecated. Only used in kuma/demos/.
@library.filter
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
