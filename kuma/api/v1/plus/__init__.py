import functools

from django.http import HttpResponseForbidden


def require_subscriber(view_function):
    @functools.wraps(view_function)
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden("not signed in")
        if not user.is_active:
            return HttpResponseForbidden("not a subscriber")
        return view_function(request, *args, **kwargs)

    return inner
