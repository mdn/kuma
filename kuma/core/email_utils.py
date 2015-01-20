import contextlib
import logging
from functools import wraps

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.test import RequestFactory
from django.utils import translation

import jingo
import tower


log = logging.getLogger('kuma.core.email')


@contextlib.contextmanager
def uselocale(locale):
    """Context manager for setting locale and returning
    to previous locale.

    This is useful for when doing translations for things run by
    celery workers or out of the HTTP request handling path.

    >>> with uselocale('xx'):
    ...     subj = _('Subject of my email')
    ...     msg = render_email(email_template, email_kwargs)
    ...     mail.send_mail(subj, msg, ...)
    ...

    In Kitsune, you can get the right locale from Profile.locale and
    also request.LANGUAGE_CODE.

    If Kitsune is handling an HTTP request already, you don't have to
    run uselocale---the locale will already be set correctly.

    """
    currlocale = translation.get_language()
    tower.activate(locale)
    yield
    tower.activate(currlocale)


def safe_translation(f):
    """Call `f` which has first argument `locale`. If `f` raises an
    exception indicative of a bad localization of a string, try again in
    `settings.WIKI_DEFAULT_LANGUAGE`.

    NB: This means `f` will be called up to two times!
    """
    @wraps(f)
    def wrapper(locale, *args, **kwargs):
        try:
            with uselocale(locale):
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

            with uselocale(settings.WIKI_DEFAULT_LANGUAGE):
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
        req = RequestFactory()
        req.META = {}
        req.locale = locale

        return jingo.render_to_string(req, template, context)

    return _render(translation.get_language())


def emails_with_users_and_watches(subject,
                                  text_template,
                                  html_template,
                                  context_vars,
                                  users_and_watches,
                                  from_email=settings.TIDINGS_FROM_ADDRESS,
                                  default_locale=settings.WIKI_DEFAULT_LANGUAGE,
                                  **extra_kwargs):
    """Return iterable of EmailMessages with user and watch values substituted.

    A convenience function for generating emails by repeatedly
    rendering a Django template with the given ``context_vars`` plus a
    ``user`` and ``watches`` key for each pair in
    ``users_and_watches``

    .. Note::

       This is a locale-aware re-write of the same function in django-tidings.
       It's kind of goofy--I ain't gonna lie.

    :arg subject: lazy gettext subject string
    :arg text_template: path to text template file
    :arg html_template: path to html template file
    :arg context_vars: a map which becomes the Context passed in to the
        template and the subject string
    :arg from_email: the from email address
    :arg default_local: the local to default to if not user.profile.locale
    :arg extra_kwargs: additional kwargs to pass into EmailMessage constructor

    :returns: generator of EmailMessage objects

    """
    @safe_translation
    def _make_mail(locale, user, watch):
        context_vars['user'] = user
        context_vars['watch'] = watch[0]
        context_vars['watches'] = watch

        msg = EmailMultiAlternatives(
            subject.format(**context_vars),
            render_email(text_template, context_vars),
            from_email,
            [user.email],
            **extra_kwargs)

        if html_template:
            msg.attach_alternative(
                render_email(html_template, context_vars), 'text/html')

        return msg

    for user, watch in users_and_watches:
        if hasattr(user, 'profile'):
            locale = user.profile.locale
        else:
            locale = default_locale

        yield _make_mail(locale, user, watch)
