# -*- coding: utf-8 -*-
import difflib
import json
import re
import urllib
import urlparse

import jinja2
from tower import ugettext as _

from django.contrib.sites.models import Site
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import conditional_escape

from constance import config
from jingo import register
from jingo_minify.helpers import get_js_urls, get_css_urls

from kuma.core.urlresolvers import reverse
from .constants import DIFF_WRAP_COLUMN
from .jobs import DocumentZoneStackJob
from .utils import tidy_content


def get_compare_url(doc, from_id, to_id):
    params = urllib.urlencode({'from': from_id, 'to': to_id})
    return (reverse('wiki.compare_revisions', args=[doc.slug],
                    locale=doc.locale) + '?' + params)


@register.filter
def bugize_text(content):
    content = jinja2.escape(content)
    regex = re.compile(r'(bug)\s+#?(\d+)', re.IGNORECASE)
    content = regex.sub(
        jinja2.Markup('<a href="https://bugzilla.mozilla.org/'
                      'show_bug.cgi?id=\\2" '
                      'target="_blank">\\1 \\2</a>'),
        content)
    return content


@register.function
def format_comment(rev, previous_revision=None):
    """
    Massages revision comment content after the fact
    """
    prev_rev = getattr(rev, 'previous_revision', previous_revision)
    if prev_rev is None:
        prev_rev = rev.previous
    comment = bugize_text(rev.comment if rev.comment else "")

    # If a page move, say so
    if prev_rev and prev_rev.slug != rev.slug:
        comment += jinja2.Markup(
            '<span class="slug-change">'
            '<span>%s</span>'
            ' <i class="icon-long-arrow-right" aria-hidden="true"></i> '
            '<span>%s</span></span>') % (prev_rev.slug, rev.slug)

    return comment


@register.function
def revisions_unified_diff(from_revision, to_revision):
    """
    Given the two revisions generate a diff between their tidied
    content in the unified diff format.
    """
    if from_revision is None or to_revision is None:
        return "Diff is unavailable."

    fromfile = '[%s] #%s' % (from_revision.document.locale, from_revision.id)
    tofile = '[%s] #%s' % (to_revision.document.locale, to_revision.id)

    tidy_from = from_revision.get_tidied_content()
    tidy_to = to_revision.get_tidied_content()

    return u'\n'.join(difflib.unified_diff(
        tidy_from.splitlines(),
        tidy_to.splitlines(),
        fromfile=fromfile,
        tofile=tofile,
    ))


@register.function
def diff_table(content_from, content_to, prev_id, curr_id, tidy=False):
    """
    Creates an HTML diff of the passed in content_from and content_to.
    """
    if tidy:
        content_from, errors = tidy_content(content_from)
        content_to, errors = tidy_content(content_to)

    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    try:
        diff = html_diff.make_table(content_from.splitlines(),
                                    content_to.splitlines(),
                                    _('Revision %s') % prev_id,
                                    _('Revision %s') % curr_id,
                                    context=True,
                                    numlines=config.DIFF_CONTEXT_LINES)
    except RuntimeError:
        # some diffs hit a max recursion error
        message = _(u'There was an error generating the content.')
        diff = '<div class="warning"><p>%s</p></div>' % message
    return jinja2.Markup(diff)


@register.function
def tag_diff_table(prev_tags, curr_tags, prev_id, curr_id):
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)

    diff = html_diff.make_table([prev_tags], [curr_tags],
                                _('Revision %s') % prev_id,
                                _('Revision %s') % curr_id)

    # Simple formatting update: 784877
    diff = diff.replace('",', '"<br />').replace('<td', '<td valign="top"')
    return jinja2.Markup(diff)


@register.function
def colorize_diff(diff):
    # we're doing something horrible here because this will show up
    # in feed reader and other clients that don't load CSS files
    diff = diff.replace('<span class="diff_add"', '<span class="diff_add" '
                        'style="background-color: #afa; text-decoration: none;"')
    diff = diff.replace('<span class="diff_sub"', '<span class="diff_sub" '
                        'style="background-color: #faa; text-decoration: none;"')
    diff = diff.replace('<span class="diff_chg"', '<span class="diff_chg" '
                        'style="background-color: #fe0; text-decoration: none;"')
    return diff


@register.filter
def wiki_bleach(val):
    from kuma.wiki.models import Document
    return jinja2.Markup(Document.objects.clean_content(val))


def _recursive_escape(value, esc=conditional_escape):
    """
    Recursively escapes strings in an object.

    Traverses dict, list and tuples. These are the data structures supported
    by the JSON encoder.
    """
    if isinstance(value, dict):
        return type(value)((esc(k), _recursive_escape(v))
                           for (k, v) in value.iteritems())
    elif isinstance(value, (list, tuple)):
        return type(value)(_recursive_escape(v) for v in value)
    elif isinstance(value, basestring):
        return esc(value)
    elif isinstance(value, (int, long, float)) or value in (True, False, None):
        return value
    # We've exhausted all the types acceptable by the default JSON encoder.
    # Django's improved JSON encoder handles a few other types, all of which
    # are represented by strings. For these types, we apply JSON encoding
    # immediately and then escape the result.
    return esc(DjangoJSONEncoder().default(value))


@register.filter
def tojson(value):
    """
    Returns the JSON representation of the value.
    """
    try:
        # If value contains custom subclasses of int, str, datetime, etc.
        # arbitrary exceptions may be raised during escaping or serialization.
        result = json.dumps(_recursive_escape(value), cls=DjangoJSONEncoder)
    except Exception:
        return ''
    return jinja2.Markup(result)


@register.function
def document_zone_management_links(user, document):
    links = {'add': None, 'change': None}
    stack = DocumentZoneStackJob().get(document.pk)
    zone = (len(stack) > 0) and stack[0] or None

    # Enable "add" link if there is no zone for this document, or if there's a
    # zone but the document is not itself the root (ie. to add sub-zones).
    if ((not zone or zone.document != document) and
            user.has_perm('wiki.add_documentzone')):
        links['add'] = '%s?document=%s' % (
            reverse('admin:wiki_documentzone_add'), document.id)

    # Enable "change" link if there's a zone, and the user has permission.
    if zone and user.has_perm('wiki.change_documentzone'):
        links['change'] = reverse('admin:wiki_documentzone_change',
                                  args=(zone.id,))

    return links


@register.filter
def absolutify(url, site=None):
    """
    Joins a base ``Site`` URL with a URL path.

    If no site provided it gets the current site from Site.

    """
    if url.startswith('http'):
        return url

    if not site:
        site = Site.objects.get_current()

    parts = urlparse.urlsplit(url)

    scheme = 'https'
    netloc = site.domain
    path = parts.path
    query = parts.query
    fragment = parts.fragment

    if path == '':
        path = '/'

    return urlparse.urlunparse([scheme, netloc, path, None, query, fragment])


@register.function
def wiki_url(path):
    """
    Create a URL pointing to Kuma.
    Look for a wiki page in the current locale, or default to given path
    """
    return reverse('wiki.document', args=[path])


def asset_url_array(asset_urls):
    """
    Return a JS array of asset URLs.
    """
    url_array = '[' + ', '.join('"%s"' % url for url in asset_urls) + ']'
    return jinja2.Markup(url_array)


@register.function
def js_url_array(bundle, debug=None):
    """
    Return a JS array of the URLS for a minified and bundled JS file.

    In production, the array will have one item, the URL of the minified,
    bundled JS file.  In development, each bundled item will be present, and
    it will be the unminified versions.

    For example, in production, 'main' returns CDN paths like:
    ["https://developer.cdn.mozilla.net/static/js/main-min.js?build=97c12a9"]

    In development, 'main' returns local paths like:
    [
      "/static/js/libs/jquery-2.1.0.js?build=1443476862,
      "/static/js/components.js?build=1443476862",
      "/static/js/analytics.js?build=1443476862",
      "/static/js/main.js?build=1443476862",
      "/static/js/auth.js?build=1443476862",
      "/static/js/libs/fontfaceobserver/" +
        "fontfaceobserver-standalone.js?build=1443476862",
      "/static/js/fonts.js?build=1443476862"
    ]
    """
    return asset_url_array(get_js_urls(bundle, debug))


@register.function
def css_url_array(bundle, debug=None):
    """
    Return a JS array of the URLS for a minified and bundled CSS file.

    Similar to js_url_array, the array will have one item in production, and
    potentially many items in development.  For example, in production 'mdn'
    returns something like:
    ["https://developer.cdn.mozilla.net/static/js/main-min.js?build=97c12a9"]

    In development, 'mdn' returns something like:
    [
      "/static/css/font-awesome.css?build=1443558726",
      "/static/css/main.css?build=1443563109"
    ]
    """
    return asset_url_array(get_css_urls(bundle, debug))
