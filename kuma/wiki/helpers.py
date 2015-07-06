# -*- coding: utf-8 -*-
import difflib
import json
import re
import urllib
import urlparse

import jinja2
from pyquery import PyQuery as pq
from tidylib import tidy_document
from tower import ugettext as _

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import conditional_escape

from constance import config
from jingo import register
from teamwork.shortcuts import build_policy_admin_links
import waffle

from kuma.core.urlresolvers import reverse
from .constants import DIFF_WRAP_COLUMN
from .jobs import DocumentZoneStackJob
from .models import Document, memcache

register.function(build_policy_admin_links)


def compare_url(doc, from_id, to_id):
    return (
        reverse('wiki.compare_revisions', args=[doc.slug],
                locale=doc.locale)
        + '?' +
        urllib.urlencode({'from': from_id, 'to': to_id})
    )


# http://stackoverflow.com/q/774316/571420
def show_diff(seqm):
    """Unify operations between two compared strings
seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    lines = config.FEED_DIFF_CONTEXT_LINES
    full_output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            full_output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            full_output.append("<ins>" + seqm.b[b0:b1] + "</ins>")
        elif opcode == 'delete':
            full_output.append("<del>" + seqm.a[a0:a1] + "</del>")
        elif opcode == 'replace':
            full_output.append("&nbsp;<del>" + seqm.a[a0:a1] + "</del>&nbsp;")
            full_output.append("&nbsp;<ins>" + seqm.b[b0:b1] + "</ins>&nbsp;")
        else:
            raise RuntimeError("unexpected opcode")
    output = []
    whitespace_change = False
    for piece in full_output:
        if '<ins>' in piece or '<del>' in piece:
            # a change
            if re.match('<(ins|del)>\W+</(ins|del)>', piece):
                # the change is whitespace,
                # ignore it and remove preceding context
                output = output[:-lines]
                whitespace_change = True
                continue
            else:
                output.append(piece)
        else:
            context_lines = piece.splitlines()
            if output == []:
                # first context only shows preceding lines for next change
                context = ['<p>...</p>'] + context_lines[-lines:]
            elif whitespace_change:
                # context shows preceding lines for next change
                context = ['<p>...</p>'] + context_lines[-lines:]
                whitespace_change = False
            else:
                # context shows subsequent lines
                # and preceding lines for next change
                context = (context_lines[:lines]
                           + ['<p>...</p>']
                           + context_lines[-lines:])
            output = output + context
    # remove extra context from the very end, unless its the only context
    if len(output) > lines + 1:  # context lines and the change line
        output = output[:-lines]
    return ''.join(output)


def _massage_diff_content(content):
    tidy_options = {
        'output-xhtml': 0,
        'force-output': 1,
    }
    try:
        content = tidy_document(content, options=tidy_options)
    except UnicodeDecodeError:
        # In case something happens in pytidylib we'll try again with
        # a proper encoding
        content = tidy_document(content.encode('utf-8'), options=tidy_options)
        tidied, errors = content
        content = tidied.decode('utf-8'), errors
    return content


@register.filter
def bugize_text(content):
    content = jinja2.escape(content)
    regex = re.compile('(bug)\s+#?(\d+)', re.IGNORECASE)
    content = regex.sub(
        jinja2.Markup('<a href="https://bugzilla.mozilla.org/'
                      'show_bug.cgi?id=\\2" '
                      'target="_blank">\\1 \\2</a>'),
        content)
    return content


@register.function
def format_comment(rev):
    """ Massages revision comment content after the fact """

    prev_rev = getattr(rev, 'previous_revision', None)
    if prev_rev is None:
        prev_rev = rev.get_previous()
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
    if from_revision is None or to_revision is None:
        return "Diff is unavailable."
    fromfile = '[%s] #%s' % (from_revision.document.locale, from_revision.id)
    tofile = '[%s] #%s' % (to_revision.document.locale, to_revision.id)
    tidy_from, errors = _massage_diff_content(from_revision.content)
    tidy_to, errors = _massage_diff_content(to_revision.content)
    return u'\n'.join(difflib.unified_diff(
        tidy_from.splitlines(),
        tidy_to.splitlines(),
        fromfile=fromfile,
        tofile=tofile,
    ))


@register.function
def diff_table(content_from, content_to, prev_id, curr_id):
    """Creates an HTML diff of the passed in content_from and content_to."""
    tidy_from, errors = _massage_diff_content(content_from)
    tidy_to, errors = _massage_diff_content(content_to)
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    from_lines = tidy_from.splitlines()
    to_lines = tidy_to.splitlines()
    try:
        diff = html_diff.make_table(from_lines, to_lines,
                                    _("Revision %s") % prev_id,
                                    _("Revision %s") % curr_id,
                                    context=True,
                                    numlines=config.DIFF_CONTEXT_LINES)
    except RuntimeError:
        # some diffs hit a max recursion error
        message = _(u'There was an error generating the content.')
        diff = '<div class="warning"><p>%s</p></div>' % message
    return jinja2.Markup(diff)


@register.function
def diff_inline(content_from, content_to):
    tidy_from, errors = _massage_diff_content(content_from)
    tidy_to, errors = _massage_diff_content(content_to)
    sm = difflib.SequenceMatcher(None, tidy_from, tidy_to)
    diff = show_diff(sm)
    return jinja2.Markup(diff)


@register.function
def tag_diff_table(prev_tags, curr_tags, prev_id, curr_id):
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    prev_tag_lines = [prev_tags]
    curr_tag_lines = [curr_tags]

    diff = html_diff.make_table(prev_tag_lines, curr_tag_lines,
                                _("Revision %s") % prev_id,
                                _("Revision %s") % curr_id)

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


@register.filter
def selector_content_find(document, selector):
    """
    Provided a selector, returns the relevant content from the document
    """
    summary = ''
    try:
        page = pq(document.rendered_html)
        summary = page.find(selector).text()
    except:
        pass
    return summary


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
@jinja2.contextfunction
def wiki_url(context, path):
    """
    Create a URL pointing to Kuma.
    Look for a wiki page in the current locale, or default to given path
    """
    request = context['request']
    if waffle.flag_is_active(request, 'dumb_wiki_urls'):
        return reverse('wiki.document', args=[path])

    default_locale = settings.WIKI_DEFAULT_LANGUAGE
    locale = getattr(request, 'locale', default_locale)

    # let's first check if the cache is already filled
    url = memcache.get(u'wiki_url:%s:%s' % (locale, path))
    if url:
        # and return the URL right away if yes
        return url

    # shortcut for when the current locale is the default one (English)
    url = reverse('wiki.document', locale=default_locale, args=[path])

    if locale != default_locale:
        # in case the current request's locale is *not* the default, e.g. 'de'
        try:
            # check if there are any translated documents in the request's
            # locale of a document with the given path and the default locale
            translation = Document.objects.get(locale=locale,
                                               parent__slug=path,
                                               parent__locale=default_locale)

            # look if the document is actual just a redirect
            redirect_url = translation.redirect_url()
            if redirect_url is None:
                # if no, build the URL of the translation
                url = translation.get_absolute_url()
            else:
                # use the redirect URL instead
                url = redirect_url
        except Document.DoesNotExist:
            # otherwise use the already defined url to the English document
            pass

    # finally cache the reversed document URL for a bit
    memcache.set(u'wiki_url:%s:%s' % (locale, path), url, 60 * 5)
    return url
