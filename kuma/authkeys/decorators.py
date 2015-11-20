import base64

from .models import Key

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps


def accepts_auth_key(func):
    """
    Enable a view to accept an auth key via HTTP Basic Auth.
    Key ID expected as username, secret as password.
    On successful auth, the request will be set with the authkey and the user
    owning the key
    """
    @wraps(func)
    def process(request, *args, **kwargs):
        request.authkey = None
        http_auth = request.META.get('HTTP_AUTHORIZATION', '')
        if http_auth:
            try:
                basic, b64_auth = http_auth.split(' ', 1)
                if 'Basic' == basic:
                    auth = base64.decodestring(b64_auth)
                    key_id, secret = auth.split(':', 1)
                    key = Key.objects.get(key=key_id)
                    if key.check_secret(secret):
                        request.authkey = key
                        request.user = key.user
            except (ValueError, Key.DoesNotExist):
                pass
        return func(request, *args, **kwargs)

    return process
