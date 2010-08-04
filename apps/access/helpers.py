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
    user = context['request'].user
    check = authority.get_check(user, perm)
    return check(obj) or user.has_perm(perm)


@register.function
@jinja2.contextfunction
def has_perm_or_owns(context, perm, obj, perm_obj, field_name='creator'):
    """
    Check if the user has a permission or owns the object.

    Ownership is determined by comparing perm_obj.field_name to the user in
    context.
    """
    user = context['request'].user
    return access.has_perm_or_owns(user, perm, obj, perm_obj, field_name) or \
           user.has_perm(perm)
