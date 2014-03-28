from django.conf import settings
from django.utils import translation


def i18n(request):
    return {'LANGUAGES': settings.LANGUAGES_DICT,
            'LANG': settings.LANGUAGE_URL_MAP.get(translation.get_language())
                    or translation.get_language(),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr',
            }


def next_url(request):
    if (hasattr(request, 'path') and
        'login' not in request.path and 'register' not in request.path):
        return {'next_url': request.get_full_path()}
    return {}
