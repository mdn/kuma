import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.test import TestCase
from django.utils.translation import trans_real

from ..cache import memcache


def assert_no_cache_header(response):
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    assert 's-maxage' not in response['Cache-Control']


def assert_shared_cache_header(response):
    assert 'public' in response['Cache-Control']
    assert 's-maxage' in response['Cache-Control']


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


def get_user(username='testuser'):
    """Return a django user or raise FixtureMissingError"""
    User = get_user_model()
    return User.objects.get(username=username)


JINJA_INSTRUMENTED = False


class KumaTestMixin(object):
    skipme = False

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
