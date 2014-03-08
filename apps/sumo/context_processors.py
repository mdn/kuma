from django.conf import settings


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}
