from django.http import HttpResponsePermanentRedirect

import jingo


def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page."""

    return jingo.render(request, 'handlers/403.html', status=403)


def handle404(request):
    """A handler for 404s that tries to strip trailing slashes before
    giving up and showing a 404 page."""

    if request.path.endswith('/'):
        fixed_path = request.path[:-1]
        query_string = request.META.get('QUERY_STRING', '')
        if query_string:
            path = '%s?%s' % (fixed_path, query_string)
        else:
            path = fixed_path

        return HttpResponsePermanentRedirect(path)

    return jingo.render(request, 'handlers/404.html', status=404)


def handle500(request):
    """A 500 message that looks nicer than the normal Apache error page."""

    return jingo.render(request, 'handlers/500.html', status=500)
