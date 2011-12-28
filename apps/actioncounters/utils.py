import re
import logging
import hashlib

from django.conf import settings

# this is not intended to be an all-knowing IP address regex
IP_RE = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


def get_ip(request):
    """
    Retrieves the remote IP address from the request data.  If the user is
    behind a proxy, they may have a comma-separated list of IP addresses, so
    we need to account for that.  In such a case, only the first IP in the
    list will be retrieved.  Also, some hosts that use a proxy will put the
    REMOTE_ADDR into HTTP_X_FORWARDED_FOR.  This will handle pulling back the
    IP from the proper place.

    **NOTE** This function was taken from django-tracking (MIT LICENSE)
             http://code.google.com/p/django-tracking/
    """

    # if neither header contain a value, just use local loopback
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR',
                                  request.META.get('REMOTE_ADDR', '127.0.0.1'))
    if ip_address:
        # make sure we have one and only one IP
        try:
            ip_address = IP_RE.match(ip_address)
            if ip_address:
                ip_address = ip_address.group(0)
            else:
                # no IP, probably from some dirty proxy or other device
                # throw in some bogus IP
                ip_address = '10.0.0.1'
        except IndexError:
            pass

    return ip_address


def get_unique(content_type, object_pk, name, request=None, ip=None, user_agent=None, user=None):
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
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255].decode('latin1', 'ignore')

    # HACK: Build a hash of the fields that should be unique, let MySQL
    # chew on that for a unique index. Note that any changes to this algo
    # will create all new unique hashes that don't match any existing ones.
    hash_text = "\n".join(unicode(x).encode('utf8') for x in (
        content_type.pk, object_pk, name, ip, user_agent, 
        (user and user.pk or 'None')
    ))
    unique_hash = hashlib.md5(hash_text).hexdigest()

    return (user, ip, user_agent, unique_hash)
