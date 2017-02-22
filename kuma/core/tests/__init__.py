import os
from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client
from django.utils.translation import trans_real

from ..cache import memcache
from ..exceptions import FixtureMissingError
from ..urlresolvers import split_path


def eq_(first, second, msg=None):
    """Rough reimplementation of nose.tools.eq_

    Note: This should be removed as soon as we no longer use it.

    """
    msg = msg or '%r != %r' % (first, second)
    assert first == second, msg


def ok_(pred, msg=None):
    """Rough reimplementation of nose.tools.ok_

    Note: This should be removed as soon as we no longer use it.

    """
    msg = msg or '%r != True' % pred
    assert pred, msg


def attrs_eq(received, **expected):
    """Compares received's attributes with expected's kwargs."""
    for k, v in expected.iteritems():
        eq_(v, getattr(received, k))


def get_user(username='testuser'):
    """Return a django user or raise FixtureMissingError"""
    User = get_user_model()
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        raise FixtureMissingError(
            'Username "%s" not found. You probably forgot to import a'
            ' users fixture.' % username)


class SessionAwareClient(Client):
    """
    Just a small override to patch the session property to be able to
    use the sessions.
    """
    def _session(self):
        """
        Obtains the current session variables.

        Backported the else clause from Django 1.7 to make sure there
        is a session available during tests.
        """
        if 'django.contrib.sessions' in settings.INSTALLED_APPS:
            engine = import_module(settings.SESSION_ENGINE)
            cookie = self.cookies.get(settings.SESSION_COOKIE_NAME, None)
            if cookie:
                return engine.SessionStore(cookie.value)
            else:
                session = engine.SessionStore()
                session.save()
                self.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
                return session
        return {}
    session = property(_session)


class LocalizingMixin(object):
    def request(self, **request):
        """Make a request, but prepend a locale if there isn't one already."""
        # Fall back to defaults as in the superclass's implementation:
        path = request.get('PATH_INFO', self.defaults.get('PATH_INFO', '/'))
        locale, shortened = split_path(path)
        if not locale:
            request['PATH_INFO'] = '/%s/%s' % (settings.LANGUAGE_CODE,
                                               shortened)
        return super(LocalizingMixin, self).request(**request)


class LocalizingClient(LocalizingMixin, SessionAwareClient):
    """Client which prepends a locale so test requests can get through
    LocaleURLMiddleware without resulting in a locale-prefix-adding 301.

    Otherwise, we'd have to hard-code locales into our tests everywhere or
    {mock out reverse() and make LocaleURLMiddleware not fire}.

    """
    # If you use this, you might also find the force_locale=True argument to
    # kuma.core.urlresolvers.reverse() handy, in case you need to force locale
    # prepending in a one-off case or do it outside a mock request.


JINJA_INSTRUMENTED = False


class KumaTestMixin(object):
    client_class = SessionAwareClient
    localizing_client = False
    skipme = False

    @classmethod
    def setUpClass(cls):
        if cls.localizing_client:
            cls.client_class = LocalizingClient
        super(KumaTestMixin, cls).setUpClass()

    def _pre_setup(self):
        super(KumaTestMixin, self)._pre_setup()

        # Clean the slate.
        cache.clear()
        memcache.clear()

        trans_real.deactivate()
        trans_real._translations = {}  # Django fails to clear this cache.
        trans_real.activate(settings.LANGUAGE_CODE)

    def get_messages(self, request):
        # Django 1.4 RequestFactory requests can't be used to test views that
        # call messages.add (https://code.djangoproject.com/ticket/17971)
        # FIXME: HACK from http://stackoverflow.com/q/11938164/571420
        messages = FallbackStorage(request)
        request._messages = messages
        return messages

    def assertFileExists(self, path):
        self.assertTrue(os.path.exists(path), u'Path %r does not exist' % path)

    def assertFileNotExists(self, path):
        self.assertFalse(os.path.exists(path), u'Path %r does exist' % path)


class KumaTestCase(KumaTestMixin, TestCase):
    pass
