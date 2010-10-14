from jingo import register
import jinja2

from . import check_watch


@register.function
@jinja2.contextfunction
def is_watching(context, obj, user=None):
    if not user:
        user = context['request'].user
    if not hasattr(user, 'email'):
        return False
    return check_watch(obj.__class__, obj.pk, user.email)
