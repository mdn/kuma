from django.conf import settings
import re
import logging

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


def get_unique(request, use_session_key=False):
    """Extract a set of unique identifiers from the request.

    This set will be made up of one of the following combinations, depending 
    on what's available:

    * user, None, None, None
    * None, None, None, session_key
    * None, ip, user_agent, None
    """
    if request.user.is_authenticated():
        user = request.user
        ip = user_agent = session_key = None
    else:
        user = None
        session_key = ( 
                ( use_session_key and hasattr(request, 'session') ) and
                request.session.session_key or None )
        if session_key:
            ip = user_agent = None
        else:
            ip = get_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    return ( user, ip, user_agent, session_key )



