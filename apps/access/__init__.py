from authority import get_check


def has_perm_or_owns(user, perm, obj, perm_obj,
                     field_name='creator'):
    """
    Given a user, a permission, an object (obj) and another object to check
    permissions against (perm_obj), returns True if the user has perm on
    obj.
    """
    if user == getattr(obj, field_name):
        return True

    check = get_check(user, perm)
    if not check:
        return False
    return check(perm_obj)
