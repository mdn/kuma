import re
from functools import wraps, partial

from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.utils.http import urlquote

from kuma.core.urlresolvers import reverse


def user_access_decorator(redirect_func, redirect_url_func, deny_func=None,
                          redirect_field=REDIRECT_FIELD_NAME):
    """
    Helper function that returns a decorator.

    * redirect func ----- If truthy, a redirect will occur
    * deny_func --------- If truthy, HttpResponseForbidden is returned.
    * redirect_url_func - Evaluated at view time, returns the redirect URL
                          i.e. where to go if redirect_func is truthy.
    * redirect_field ---- What field to set in the url, defaults to Django's.
                          Set this to None to exclude it from the URL.

    """
    def decorator(view_fn):
        def _wrapped_view(request, *args, **kwargs):
            if redirect_func(request.user):
                # We must call reverse at the view level, else the threadlocal
                # locale prefixing doesn't take effect.
                redirect_url = redirect_url_func() or reverse('account_login')

                # Redirect back here afterwards?
                if redirect_field:
                    path = urlquote(request.get_full_path())
                    redirect_url = '%s?%s=%s' % (
                        redirect_url, redirect_field, path)

                return HttpResponseRedirect(redirect_url)

            if deny_func and deny_func(request.user):
                return HttpResponseForbidden()

            return view_fn(request, *args, **kwargs)
        return wraps(view_fn, assigned=available_attrs(view_fn))(_wrapped_view)

    return decorator


def logout_required(redirect):
    """Requires that the user *not* be logged in."""
    redirect_func = lambda u: u.is_authenticated()
    if hasattr(redirect, '__call__'):
        return user_access_decorator(
            redirect_func, redirect_field=None,
            redirect_url_func=lambda: reverse('home'))(redirect)
    else:
        return user_access_decorator(redirect_func, redirect_field=None,
                                     redirect_url_func=lambda: redirect)


def login_required(func, login_url=None, redirect=REDIRECT_FIELD_NAME,
                   only_active=True):
    """Requires that the user is logged in."""
    if only_active:
        redirect_func = lambda u: not (u.is_authenticated() and u.is_active)
    else:
        redirect_func = lambda u: not u.is_authenticated()
    redirect_url_func = lambda: login_url
    return user_access_decorator(redirect_func, redirect_field=redirect,
                                 redirect_url_func=redirect_url_func)(func)


def permission_required(perm, login_url=None, redirect=REDIRECT_FIELD_NAME,
                        only_active=True):
    """A replacement for django.contrib.auth.decorators.permission_required
    that doesn't ask authenticated users to log in."""
    redirect_func = lambda u: not u.is_authenticated()
    if only_active:
        deny_func = lambda u: not (u.is_active and u.has_perm(perm))
    else:
        deny_func = lambda u: not u.has_perm(perm)
    redirect_url_func = lambda: login_url

    return user_access_decorator(redirect_func, redirect_field=redirect,
                                 redirect_url_func=redirect_url_func,
                                 deny_func=deny_func)


# django never_cache isn't as thorough as we might like
# http://stackoverflow.com/a/2095648/571420
# http://stackoverflow.com/a/2068407/571420
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching_FAQ
# Fixed in Django 1.9:
# https://docs.djangoproject.com/en/1.9/topics/http/decorators/#caching
def never_cache(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        resp = view_func(request, *args, **kwargs)

        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp['Pragma'] = 'no-cache'
        resp['Expires'] = '0'

        return resp

    return _wrapped_view_func


def is_superuser(u):
    if u.is_authenticated():
        if u.is_superuser:
            return True
        raise PermissionDenied
    return False


superuser_required = user_passes_test(is_superuser)
#: A decorator to use for requiring a superuser


def block_user_agents(view_func):
    blockable_user_agents = getattr(settings, 'BLOCKABLE_USER_AGENTS', [])
    blockable_ua_patterns = []
    for agent in blockable_user_agents:
        blockable_ua_patterns.append(re.compile(agent))

    def agent_blocked_view(request, *args, **kwargs):
        http_user_agent = request.META.get('HTTP_USER_AGENT', None)
        if http_user_agent is not None:
            for pattern in blockable_ua_patterns:
                if pattern.search(request.META['HTTP_USER_AGENT']):
                    return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    return wraps(view_func,
                 assigned=available_attrs(view_func))(agent_blocked_view)


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
    to the maintenance-mode view on requests using the given HTTP "methods"
    (or all HTTP methods if "methods" is None). Otherwise, call the
    wrapped view function as usual.
    """
    if not func:
        return partial(redirect_in_maintenance_mode, methods=methods)

    @wraps(func)
    def wrapped(request, *args, **kwargs):
        if (settings.MAINTENANCE_MODE and
                ((methods is None) or (request.method in methods))):
            return redirect('maintenance_mode')
        return func(request, *args, **kwargs)

    return wrapped
