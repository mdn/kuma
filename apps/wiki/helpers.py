# coding=utf-8

import difflib
import re
import urllib

import constance.config
from jingo import register
import jinja2
from pyquery import PyQuery as pq
from tidylib import tidy_document
from tower import ugettext as _
import logging

from django.utils.html import strip_tags
from sumo.urlresolvers import reverse
import wiki
from wiki import DIFF_WRAP_COLUMN


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


def diff_word_count(seqm):
    """Gives diff in terms of words added/removed of
    a difflib.SequenceMatcher instance """
    words = [0, 0]
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'insert':
            words[0] += len(re.findall(r'\w+', seqm.b[b0:b1]))
        elif opcode == 'delete':
            words[1] += len(re.findall(r'\w+', seqm.b[a0:a1]))
        elif opcode == 'replace':
            words[0] += len(re.findall(r'\w+', seqm.b[a0:a1]))
            words[1] += len(re.findall(r'\w+', seqm.b[b0:b1]))
    return words


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

    prev_rev = rev.get_previous()
    comment = bugize_text(rev.comment if rev.comment else "")

    #  If a page move, say so
    if prev_rev and prev_rev.slug != rev.slug:
        comment += jinja2.Markup('<span class="slug-change">'
                                 'Moved From <strong>%s</strong> '
                                 'to <strong>%s</strong></span>') % (
                                     prev_rev.slug, rev.slug)

    return comment


@register.function
def comment_diff_percent(rev):
    """Gives percentage of changed comparing with previous revision """
    prev_rev = rev.get_previous()
    message = ''
    if prev_rev:
        tidy_from, errors = _massage_diff_content(prev_rev.content)
        tidy_to, errors = _massage_diff_content(rev.content)
        sm = difflib.SequenceMatcher(None, tidy_from, tidy_to)
        ratio = 1 - sm.quick_ratio()
        percent = round(ratio, 4) * 100
        message = _(u'%s%% change in content.' % percent)
    return message


@register.function
def comment_diff_words(rev):
    """Gives words added/removed after comparing with previous revision """
    prev_rev = rev.get_previous()
    message = ''
    if prev_rev:
        # Remove line-breaks, tabs and all tags
        regex = re.compile(r'[\n\r\t]')
        tidy_from = regex.sub(' ', strip_tags(prev_rev.content))
        tidy_to = regex.sub(' ', strip_tags(rev.content))

        sm = difflib.SequenceMatcher(None, tidy_from, tidy_to)
        words = diff_word_count(sm)
        message = _(u'%s words added, %s words removed.' % (words[0], words[1]))
    return message


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
    from wiki.models import Document
    return jinja2.Markup(Document.objects.clean_content(val))
