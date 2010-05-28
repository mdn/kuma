from jingo import register
import jinja2

from . import check_watch


@register.function
@jinja2.contextfunction
def is_watching(context, obj):
    return check_watch(obj.__class__, obj.id, context['request'].user.email)
