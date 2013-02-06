from django.conf import settings
from django.utils import translation


def i18n(request):
    return {'LANGUAGES': settings.LANGUAGES,
            'LANG': settings.LANGUAGE_URL_MAP.get(translation.get_language())
                    or translation.get_language(),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr',
            }


def next_url(request):
    if 'login' not in request.path and 'register' not in request.path:
        return {'next_url': request.get_full_path()}
    return {}


def phpbb_logged_in(request):
    """Detect PHPBB login cookie."""
    return {
        'PHPBB_LOGGED_IN': (request.COOKIES.get(
            '%s_u' % settings.PHPBB_COOKIE_PREFIX, '1') != '1'),
        'PHPBB_SID': request.COOKIES.get(
            '%s_sid' % settings.PHPBB_COOKIE_PREFIX),
    }
