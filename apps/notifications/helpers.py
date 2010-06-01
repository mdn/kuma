from jingo import register
import jinja2

from . import check_watch


@register.function
@jinja2.contextfunction
def is_watching(context, obj):
    if not hasattr(context['request'].user, 'email'):
        return False
    return check_watch(obj.__class__, obj.pk, context['request'].user.email)
