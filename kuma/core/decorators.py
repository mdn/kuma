from functools import partial, wraps

from django.conf import settings
from django.shortcuts import redirect

from .utils import add_shared_cache_control


def shared_cache_control(func=None, **kwargs):
    """
    Decorator to set Cache-Control header for shared caches like CDNs.

    This duplicates Django's cache-control decorators, but avoids changing the
    header if a "no-cache" header has already been applied. The cache-control
    decorator changes in Django 2.0 to remove Python 2 workarounds.

    Default settings (which can be overridden or extended):
    - max-age=0 - Don't use browser cache without asking if still valid
    - s-maxage=CACHE_CONTROL_DEFAULT_SHARED_MAX_AGE - Cache in the shared
      cache for the default perioid of time
    - public - Allow intermediate proxies to cache response
    """

    def _shared_cache_controller(viewfunc):
        @wraps(viewfunc)
        def _cache_controlled(request, *args, **kw):
            response = viewfunc(request, *args, **kw)
            add_shared_cache_control(response, **kwargs)
            return response

        return _cache_controlled

    if func:
        return _shared_cache_controller(func)
    return _shared_cache_controller


def skip_in_maintenance_mode(func):
    """
    Decorator for Celery task functions. If we're in MAINTENANCE_MODE, skip
    the call to the decorated function. Otherwise, call the decorated function
    as usual.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        if settings.MAINTENANCE_MODE:
            return
        return func(*args, **kwargs)

    return wrapped


def redirect_in_maintenance_mode(func=None, methods=None):
    """
    Decorator for view functions. If we're in MAINTENANCE_MODE, redirect
    to the home page on requests using the given HTTP "methods" (or all
    HTTP methods if "methods" is None). Otherwise, call the wrapped view
    function as usual.
    """
    if not func:
        return partial(redirect_in_maintenance_mode, methods=methods)

    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if settings.MAINTENANCE_MODE and (
            (methods is None) or (request.method in methods)
        ):
            locale = getattr(request, "LANGUAGE_CODE", None)
            return redirect(f"/{locale}/" if locale else "/")
        return func(request, *args, **kwargs)

    return wrapped
