# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
    return access.has_perm(context['request'].user, perm, obj)


@register.function
@jinja2.contextfunction
def has_perm_or_owns(context, perm, obj, perm_obj, field_name='creator'):
    """
    Check if the user has a permission or owns the object.

    Ownership is determined by comparing perm_obj.field_name to the user in
    context.
    """
    user = context['request'].user
    return access.has_perm_or_owns(user, perm, obj, perm_obj, field_name)
