import logging
from functools import wraps

from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import translation


log = logging.getLogger("kuma.core.email")


def safe_translation(f):
    """Call `f` which has first argument `locale`. If `f` raises an
    exception indicative of a bad localization of a string, try again in
    `settings.WIKI_DEFAULT_LANGUAGE`.

    NB: This means `f` will be called up to two times!
    """

    @wraps(f)
    def wrapper(locale, *args, **kwargs):
        try:
            with translation.override(locale):
                return f(locale, *args, **kwargs)
        except (TypeError, KeyError, ValueError, IndexError) as e:
            # Types of errors, and examples.
            #
            # TypeError: Not enough arguments for string
            #   '%s %s %s' % ('foo', 'bar')
            # KeyError: Bad variable name
            #   '%(Foo)s' % {'foo': 10} or '{Foo}'.format(foo=10')
            # ValueError: Incomplete Format, or bad format string.
            #    '%(foo)a' or '%(foo)' or '{foo'
            # IndexError: Not enough arguments for .format() style string.
            #    '{0} {1}'.format(42)
            log.error('Bad translation in locale "%s": %s', locale, e)

            with translation.override(settings.WIKI_DEFAULT_LANGUAGE):
                return f(settings.WIKI_DEFAULT_LANGUAGE, *args, **kwargs)

    return wrapper


def render_email(template, context):
    """Renders a template in the currently set locale.

    Falls back to WIKI_DEFAULT_LANGUAGE in case of error.
    """

    @safe_translation
    def _render(locale):
        """Render an email in the given locale.

        Because of safe_translation decorator, if this fails,
        the function will be run again in English.
        """
        req = RequestFactory().get("/")
        req.META = {}
        req.LANGUAGE_CODE = locale

        return render_to_string(template, context, request=req)

    return _render(translation.get_language())
