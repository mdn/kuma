import constance.config
from difflib import HtmlDiff
from jingo import register
import jinja2

from wiki import DIFF_WRAP_COLUMN
from wiki import parser


@register.function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    html_diff = HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    from_lines = content_from.splitlines()
    to_lines = content_to.splitlines()
    diff = html_diff.make_table(from_lines, to_lines, context=True,
                                numlines=constance.config.DIFF_CONTEXT_LINES)
    return jinja2.Markup(diff)


@register.function
def generate_video(v):
    return jinja2.Markup(parser.generate_video(v))
