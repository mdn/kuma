from django.conf import settings
from django.utils import translation

from .i18n import get_language_mapping


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def i18n(request):
    return {
        'LANGUAGES': get_language_mapping(),
        'LANG': (settings.LANGUAGE_URL_MAP.get(translation.get_language()) or
                 translation.get_language()),
        'DIR': 'rtl' if translation.get_language_bidi() else 'ltr',
    }


def next_url(request):
    if (hasattr(request, 'path') and
            'login' not in request.path and
            'register' not in request.path):
        return {'next_url': request.get_full_path()}
    return {}
