import difflib
import re

import constance.config
from jingo import register
import jinja2
from tidylib import tidy_document

from wiki import DIFF_WRAP_COLUMN
from wiki import parser


# http://stackoverflow.com/q/774316/571420
def show_diff(seqm):
    """Unify operations between two compared strings
seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    lines = constance.config.FEED_DIFF_CONTEXT_LINES
    full_output= []
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
            raise RuntimeError, "unexpected opcode"
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
                context = context_lines[:lines] + ['<p>...</p>'] + context_lines[-lines:]
            output = output + context
    # remove extra context from the very end, unless its the only context
    if len(output) > lines+1:  # context lines and the change line
        output = output[:-lines]
    return ''.join(output)

@register.function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    tidy_options = {'output-xhtml': 0, 'force-output': 1}
    tidy_from, errors = tidy_document(content_from, options=tidy_options)
    tidy_to, errors = tidy_document(content_to, options=tidy_options)
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    from_lines = tidy_from.splitlines()
    to_lines = tidy_to.splitlines()
    diff = html_diff.make_table(from_lines, to_lines, context=True,
                                numlines=constance.config.DIFF_CONTEXT_LINES)
    return jinja2.Markup(diff)

@register.function
def diff_inline(content_from, content_to):
    sm = difflib.SequenceMatcher(None, content_from, content_to)
    diff = show_diff(sm)
    return jinja2.Markup(diff)


@register.function
def generate_video(v):
    return jinja2.Markup(parser.generate_video(v))
