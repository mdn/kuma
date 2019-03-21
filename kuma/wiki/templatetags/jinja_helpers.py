# -*- coding: utf-8 -*-
import difflib
import json
import re

import jinja2
from constance import config
from cssselect.parser import SelectorSyntaxError
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.template import loader
from django.utils import lru_cache
from django.utils.html import conditional_escape
from django.utils.six.moves.urllib.parse import urlsplit, urlunparse
from django.utils.translation import ugettext
from django_jinja import library
from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse
from kuma.core.utils import order_params, urlparams

from ..constants import DIFF_WRAP_COLUMN
from ..content import clean_content
from ..utils import tidy_content


def get_compare_url(doc, from_id, to_id):
    return order_params(urlparams(
        reverse('wiki.compare_revisions', args=[doc.slug], locale=doc.locale),
        **{'from': from_id, 'to': to_id}
    ))


@library.filter
def bugize_text(content):
    content = jinja2.escape(content)
    regex = re.compile(r'(bug)\s+#?(\d+)', re.IGNORECASE)
    content = regex.sub(
        jinja2.Markup('<a href="https://bugzilla.mozilla.org/'
                      'show_bug.cgi?id=\\2" '
                      'target="_blank">\\1 \\2</a>'),
        content)
    return content


@library.global_function
def format_comment(rev, previous_revision=None, load_previous=True):
    """
    Format comment for HTML display, with Bugzilla links and slug changes.

    Keyword Arguments:
    rev - The revision
    previous_revision - The previous revision (default None)
    load_previous - Try loading previous revision if None (default True)
    """
    if previous_revision is None and load_previous:
        previous_revision = rev.previous
    comment = bugize_text(rev.comment if rev.comment else "")

    # If a page move, say so
    if previous_revision and previous_revision.slug != rev.slug:
        comment += jinja2.Markup(
            '<span class="slug-change">'
            '<span>%s</span>'
            ' <i class="icon-long-arrow-right" aria-hidden="true"></i> '
            '<span>%s</span></span>') % (previous_revision.slug, rev.slug)

    return comment


@library.global_function
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


@library.global_function
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
                                    ugettext('Revision %s') % prev_id,
                                    ugettext('Revision %s') % curr_id,
                                    context=True,
                                    numlines=config.DIFF_CONTEXT_LINES)
    except RuntimeError:
        # some diffs hit a max recursion error
        message = ugettext(u'There was an error generating the content.')
        diff = '<div class="warning"><p>%s</p></div>' % message
    return jinja2.Markup(diff)


@library.global_function
def tag_diff_table(prev_tags, curr_tags, prev_id, curr_id):
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)

    diff = html_diff.make_table([prev_tags], [curr_tags],
                                ugettext('Revision %s') % prev_id,
                                ugettext('Revision %s') % curr_id)

    # Simple formatting update: 784877
    diff = diff.replace('",', '"<br />').replace('<td', '<td valign="top"')
    return jinja2.Markup(diff)


@library.global_function
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


@library.filter
def wiki_bleach(val):
    return jinja2.Markup(clean_content(val))


@library.filter
def selector_content_find(document, selector):
    """
    Provided a selector, returns the relevant content from the document
    """
    content = ''
    try:
        page = pq(document.rendered_html)
    except ValueError:
        # pass errors during construction
        pass
    try:
        content = page.find(selector).text()
    except SelectorSyntaxError:
        # pass errors during find/select
        pass
    return content


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


@library.filter
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


@library.filter
def absolutify(url):
    """Joins settings.SITE_URL with a URL path."""
    if url.startswith('http'):
        return url

    site = urlsplit(settings.SITE_URL)
    parts = urlsplit(url)
    scheme = site.scheme
    netloc = site.netloc
    path = parts.path
    query = parts.query
    fragment = parts.fragment

    if path == '':
        path = '/'

    return urlunparse([scheme, netloc, path, None, query, fragment])


@library.global_function
def wiki_url(path):
    """
    Create a URL pointing to Kuma.
    Look for a wiki page in the current locale, or default to given path
    """
    if '#' in path:
        slug, fragment = path.split('#', 1)
    else:
        slug = path
        fragment = ''
    new_path = reverse('wiki.document', args=[slug])
    if fragment:
        new_path += '#' + fragment
    return new_path


@library.global_function
@lru_cache.lru_cache()
def include_svg(path, title=None, title_id=None):
    """
    Embded an SVG file by path, optionally changing the title,
    and adding an id
    """
    svg = loader.get_template(path).render()
    if (title):
        svg_parsed = pq(svg, namespaces={'svg': 'http://www.w3.org/2000/svg'})
        svg_parsed('svg|title')[0].text = title
        if (title_id):
            svg_parsed('svg|title').attr['id'] = title_id
        svg_out = svg_parsed.outerHtml()
    else:
        svg_out = svg
    return jinja2.Markup(svg_out)
