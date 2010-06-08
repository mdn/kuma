import authority
import jinja2
from jingo import register

import access


@register.function
@jinja2.contextfunction
def has_perm(context, perm, obj):
    """
    Check if the user has a permission on a specific object.

    Returns boolean.
    """
    check = authority.get_check(context['request'].user, perm)
    return check(obj)


@register.function
@jinja2.contextfunction
def has_perm_or_owns(context, perm, obj, perm_obj, field_name='creator'):
    """
    Check if the user has a permission or owns the object.

    Ownership is determined by comparing perm_obj.field_name to the user in
    context.
    """
    return access.has_perm_or_owns(context['request'].user, perm, obj,
                                   perm_obj, field_name)
