from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import (
    LocalePrefixPattern,
    reverse as django_reverse,
    URLResolver,
)
from django.utils import translation

from .i18n import get_language


class KumaLocalePrefixPattern(LocalePrefixPattern):
    """
    A prefix pattern for localized URLs that uses Kuma's case-sensitive locale
    codes instead of Django's, which are all lowercase.

    We do this via a customized get_language function in kuma/core/i18n.py.

    NOTE: See upstream LocalePrefixPattern for Django 2.2 / 3.0:
    https://github.com/django/django/blob/3.0/django/urls/resolvers.py#L288-L319
    """

    @property
    def language_prefix(self):
        language_code = get_language() or settings.LANGUAGE_CODE
        return "%s/" % language_code


def i18n_patterns(*urls):
    """
    Add the language code prefix to every URL pattern within this function.
    This may only be used in the root URLconf, not in an included URLconf.

    NOTE: Modified from i18n_patterns in Django 2.2 / 3.0, see:
    https://github.com/django/django/blob/3.0/django/conf/urls/i18n.py#L8-L20

    Modifications:
    - Raises ImproperlyConfigured if settings.USE_I18N is False
    - Forces prefix_default_language to True, so urls always include the locale
    - Does not accept prefix_default_language as a kwarg, due to the above
    - Uses our custom URL prefix pattern, to support our locale codes
    """
    if not settings.USE_I18N:
        raise ImproperlyConfigured("Kuma requires settings.USE_I18N to be True.")
    return [URLResolver(KumaLocalePrefixPattern(), list(urls))]


def reverse(
    viewname, urlconf=None, args=None, kwargs=None, current_app=None, locale=None
):
    """Wraps Django's reverse to prepend the requested locale.
    Keyword Arguments:
    * locale - Use this locale prefix rather than the current active locale.
    Keyword Arguments passed to Django's reverse:
    * viewname
    * urlconf
    * args
    * kwargs
    * current_app
    """
    if locale:
        with translation.override(locale):
            return django_reverse(
                viewname,
                urlconf=urlconf,
                args=args,
                kwargs=kwargs,
                current_app=current_app,
            )
    else:
        return django_reverse(
            viewname, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app
        )
