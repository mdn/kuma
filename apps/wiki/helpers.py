from difflib import HtmlDiff

import jinja2
from jingo import register

from wiki import DIFF_WRAP_COLUMN
from wiki import parser


@register.function
def diff_table(content_from, content_to):
    """Creates an HTML diff of the passed in content_from and content_to."""
    html_diff = HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    diff = html_diff.make_table(content_from.splitlines(),
                                content_to.splitlines(), context=True)
    return jinja2.Markup(diff)


@register.function
def generate_video(v):
    return jinja2.Markup(parser.generate_video(v))
