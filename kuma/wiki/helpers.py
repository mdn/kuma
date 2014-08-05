# coding=utf-8

import json
import difflib
import re
import urllib

import jinja2
from pyquery import PyQuery as pq
from tidylib import tidy_document
from tower import ugettext as _

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import conditional_escape

import constance.config
from jingo import register
from teamwork.shortcuts import build_policy_admin_links

from sumo.urlresolvers import reverse
from .constants import DIFF_WRAP_COLUMN


register.function(build_policy_admin_links)


def compare_url(doc, from_id, to_id):
    return (reverse('wiki.compare_revisions', args=[doc.full_path],
                    locale=doc.locale)
            + '?' +
            urllib.urlencode({'from': from_id, 'to': to_id})
           )


# http://stackoverflow.com/q/774316/571420
def show_diff(seqm):
    """Unify operations between two compared strings
seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    lines = constance.config.FEED_DIFF_CONTEXT_LINES
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
    tidy_options = {'output-xhtml': 0, 'force-output': 1}
    content = tidy_document(content, options=tidy_options)
    return content


@register.filter
def bugize_text(content):
    content = jinja2.escape(content)
    content = re.sub(r'bug\s+#?(\d+)',
                  jinja2.Markup('<a href="https://bugzilla.mozilla.org/'
                                'show_bug.cgi?id=\\1" '
                                'target="_blank">bug \\1</a>'),
                  content)
    return content


@register.function
def format_comment(rev):
    """ Massages revision comment content after the fact """

    prev_rev = getattr(rev, 'previous_revision', None)
    if prev_rev is None:
        prev_rev = rev.get_previous()
    comment = bugize_text(rev.comment if rev.comment else "")

    #  If a page move, say so
    if prev_rev and prev_rev.slug != rev.slug:
        comment += (jinja2.Markup('<span class="slug-change">'
                                  '<span>%s</span>'
                                  ' <i class="icon-long-arrow-right" aria-hidden="true"></i> '
                                  '<span>%s</span></span>') % (prev_rev.slug, rev.slug))

    return comment


@register.function
def revisions_unified_diff(from_revision, to_revision):
    if from_revision is None or to_revision is None:
        return "Diff is unavailable."
    fromfile = u'[%s] %s #%s' % (from_revision.document.locale,
                                 from_revision.document.title,
                                 from_revision.id)
    tofile = u'[%s] %s #%s' % (to_revision.document.locale,
                               to_revision.document.title,
                               to_revision.id)
    tidy_from, errors = _massage_diff_content(from_revision.content)
    tidy_to, errors = _massage_diff_content(to_revision.content)
    diff = u'\n'.join(difflib.unified_diff(
        tidy_from.splitlines(),
        tidy_to.splitlines(),
        fromfile=fromfile,
        tofile=tofile
    ))
    return diff


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
                                numlines=constance.config.DIFF_CONTEXT_LINES
                               )
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
                                _("Revision %s") % curr_id
                               )

    # Simple formatting update: 784877
    diff = diff.replace('",', '"<br />').replace('<td', '<td valign="top"')
    return jinja2.Markup(diff)


@register.function
def colorize_diff(diff):
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
    stack = document.find_zone_stack()
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
