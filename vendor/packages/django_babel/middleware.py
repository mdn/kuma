# -*- coding: utf-8 -*-

from babel import Locale, UnknownLocaleError
from django.utils.translation import get_language
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local


__all__ = ['get_current_locale', 'LocaleMiddleware']

_thread_locals = local()


def get_current_locale():
    """Get current locale data outside views.

    See http://babel.pocoo.org/docs/api/core/#babel.core.Locale for Locale
    objects documentation
    """
    return getattr(_thread_locals, 'locale', None)


class LocaleMiddleware(object):

    """Simple Django middleware that makes available a Babel `Locale` object
    via the `request.locale` attribute.
    """

    def process_request(self, request):
        try:
            code = getattr(request, 'LANGUAGE_CODE', get_language())
            locale = Locale.parse(code, sep='-')
        except (ValueError, UnknownLocaleError):
            pass
        else:
            _thread_locals.locale = request.locale = locale
