from dbgettext.parser import parsed_gettext as _parsed_gettext
from django import template

register = template.Library()

@register.filter
def parsed_gettext(obj, attribute):
    return _parsed_gettext(obj, attribute)
