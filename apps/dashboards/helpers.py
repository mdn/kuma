from jinja2 import Markup
from jingo import register

any_ = any


@register.function
def any(iterable):
    return any_(iterable)


@register.function
def selected(a, b, text=None):
    text = text or ' selected="selected"'
    return Markup(text if a == b else '')
