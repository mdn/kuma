from django import http


def landing(request):
    """Customer Care Landing page."""
    return http.HttpResponse(landing.__doc__)
