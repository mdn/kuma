import hashlib

from kuma.core.utils import get_ip


def get_unique(content_type, object_pk, request=None, ip=None, user_agent=None, user=None):
    """Extract a set of unique identifiers from the request.

    This set will be made up of one of the following combinations, depending
    on what's available:

    * user, None, None, unique_MD5_hash
    * None, ip, user_agent, unique_MD5_hash
    """
    if request:
        if request.user.is_authenticated():
            user = request.user
            ip = user_agent = None
        else:
            user = None
            ip = get_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    # HACK: Build a hash of the fields that should be unique, let MySQL
    # chew on that for a unique index. Note that any changes to this algo
    # will create all new unique hashes that don't match any existing ones.
    hash_text = "\n".join(unicode(x).encode('utf8') for x in (
        content_type.pk, object_pk, ip, user_agent,
        (user and user.pk or 'None')
    ))
    unique_hash = hashlib.md5(hash_text).hexdigest()

    return (user, ip, user_agent, unique_hash)
