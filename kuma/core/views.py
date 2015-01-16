from django.shortcuts import render


def _error_page(request, status):
    """Render error pages with jinja2."""
    return render(request, '%d.html' % status, status=status)

handler403 = lambda request: _error_page(request, 403)
handler404 = lambda request: _error_page(request, 404)
handler500 = lambda request: _error_page(request, 500)
