from jinja2 import Markup
from jingo import register


@register.function
def selected(a, b, text=None):
    text = text or ' selected="selected"'
    return Markup(text if a == b else '')
