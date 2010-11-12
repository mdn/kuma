from difflib import HtmlDiff

from jingo import register
import jinja2

from notifications import check_watch
from wiki import DIFF_WRAP_COLUMN
from wiki import parser
from wiki.models import Document


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


@register.function
def is_watching_locale(user, locale):
    """Check if the user is watching documents in the locale."""
    return check_watch(Document, None, user.email, 'ready_for_review', locale)
