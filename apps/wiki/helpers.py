import difflib

from jingo import register
import jinja2

from wiki import DIFF_WRAP_COLUMN
from wiki import parser


# http://stackoverflow.com/q/774316/571420
def show_diff(seqm):
    """Unify operations between two compared strings
seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
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
    for piece in full_output:
        if '<ins>' in piece or '<del>' in piece:
            # a change piece, so include it as-is
            output.append(piece)
        '''
        else:
            context_lines = piece.splitlines()
            if output == []:  # first context only shows preceding 3 lines
                context = ['<p>...</p>'] + context_lines[-3:]
            else:  # context shows subsequent and preceding lines
                context = context_lines[:3] + ['<p>...</p>'] + context_lines[-3:]
            output = output + context
        '''
    return ''.join(output)

@register.function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    diff = html_diff.make_table(content_from.splitlines(),
                                content_to.splitlines(), context=True)
    return jinja2.Markup(diff)

@register.function
def diff_inline(content_from, content_to):
    sm = difflib.SequenceMatcher(None, content_from, content_to)
    diff = show_diff(sm)
    return jinja2.Markup(diff)


@register.function
def generate_video(v):
    return jinja2.Markup(parser.generate_video(v))
