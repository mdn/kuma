from functools import wraps

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs


def ssl_required(view_func):
    """A view decorator that enforces HTTPS.

    If settings.DEBUG is True, it doesn't enforce anything."""
    def _checkssl(request, *args, **kwargs):
        if not settings.DEBUG and not request.is_secure():
            url_str = request.build_absolute_uri()
            url_str = url_str.replace('http://', 'https://')
            return HttpResponseRedirect(url_str)

        return view_func(request, *args, **kwargs)
    return _checkssl


def logout_required(redirect='/'):
    """Requires that the user *not* be logged in."""
    callable = False
    if hasattr(redirect, '__call__'):
        callable = True
        view = redirect
        redirect = '/'

    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if request.user and request.user.is_authenticated():
                return HttpResponseRedirect(redirect)
            return view_func(request, *args, **kwargs)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped)

    if callable:
        return decorator(view)
    return decorator
