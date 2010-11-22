from django.conf import settings
from django.http import HttpResponseRedirect


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
