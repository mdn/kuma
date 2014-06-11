from django.conf import settings, UserSettingsHolder
from django.utils.functional import wraps
from django.test.client import Client

import constance.config
from constance.backends import database as constance_database

import test_utils
from nose.plugins.skip import SkipTest

from sumo.urlresolvers import split_path


class SkippedTestCase(test_utils.TestCase):
    def setUp(self):
        raise SkipTest()


class overrider(object):
    """
    See http://djangosnippets.org/snippets/2437/

    Acts as either a decorator, or a context manager.  If it's a decorator it
    takes a function and returns a wrapped function.  If it's a contextmanager
    it's used with the ``with`` statement.  In either event entering/exiting
    are called before and after, respectively, the function/block is executed.
    """
    def __init__(self, **kwargs):
        self.options = kwargs

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disable()

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return inner

    def enable(self):
        pass

    def disable(self):
        pass


class override_constance_settings(overrider):
    """Decorator / context manager to override constance settings and defeat
    its caching."""

    def enable(self):
        self.old_cache = constance_database.db_cache
        constance_database.db_cache = None
        self.old_settings = dict((k, getattr(constance.config, k))
                                 for k in dir(constance.config))
        for k, v in self.options.items():
            constance.config._backend.set(k, v)

    def disable(self):
        for k, v in self.old_settings.items():
            constance.config._backend.set(k, v)
        constance_database.db_cache = self.old_cache


class override_settings(overrider):
    """Decorator / context manager to override Django settings"""

    def enable(self):
        self.old_settings = settings._wrapped
        override = UserSettingsHolder(settings._wrapped)
        for key, new_value in self.options.items():
            setattr(override, key, new_value)
        settings._wrapped = override

    def disable(self):
        settings._wrapped = self.old_settings

def mock_lookup_user():
    return {u'confirmed': True,
            u'country': u'us',
            u'created-date': u'12/8/2013 8:05:55 AM',
            u'email': u'testuser@test.com',
            u'format': u'H',
            u'lang': u'en-US',
            u'master': True,
            u'newsletters': [],
            u'pending': False,
            u'status': u'ok',
            u'token': u'cdaa9e5d-2023-5f59-974d-83f6a29514ec'}


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


class LocalizingClient(LocalizingMixin, Client):
    """Client which prepends a locale so test requests can get through
    LocaleURLMiddleware without resulting in a locale-prefix-adding 301.

    Otherwise, we'd have to hard-code locales into our tests everywhere or
    {mock out reverse() and make LocaleURLMiddleware not fire}.

    """

    # If you use this, you might also find the force_locale=True argument to
    # sumo.urlresolvers.reverse() handy, in case you need to force locale
    # prepending in a one-off case or do it outside a mock request.
