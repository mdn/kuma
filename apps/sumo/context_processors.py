from django.conf import settings


def title(request):
    """Adds site title to the context."""
    return {'SITE_TITLE': settings.SITE_TITLE}


def auth(request):
    """Adds auth-related urls to the context."""
    return {'LOGIN_URL': settings.LOGIN_URL, 'LOGOUT_URL': settings.LOGOUT_URL}
