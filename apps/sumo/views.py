from django.http import HttpResponsePermanentRedirect

import jingo


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
