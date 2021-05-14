import os
from functools import wraps
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils.translation import trans_real


def assert_no_cache_header(response):
    assert "max-age=0" in response["Cache-Control"]
    assert "no-cache" in response["Cache-Control"]
    assert "no-store" in response["Cache-Control"]
    assert "must-revalidate" in response["Cache-Control"]
    assert "s-maxage" not in response["Cache-Control"]


def assert_shared_cache_header(response):
    assert "public" in response["Cache-Control"]
    assert "s-maxage" in response["Cache-Control"]


def get_user(username="testuser"):
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

        trans_real.deactivate()
        trans_real._translations = {}  # Django fails to clear this cache.
        trans_real.activate(settings.LANGUAGE_CODE)

    def assertFileExists(self, path):
        self.assertTrue(os.path.exists(path), "Path %r does not exist" % path)

    def assertFileNotExists(self, path):
        self.assertFalse(os.path.exists(path), "Path %r does exist" % path)


class KumaTestCase(KumaTestMixin, TestCase):
    pass


def call_on_commit_immediately(test_method):
    """Useful for TestCase test methods, that ultimately depends on
    `transaction.on_commit()` being called somewhere in the stack. These
    would normally be not executed when TestCase rolls back.
    But if the test wants to assert that something inside a
    `transaction.on_commit()` is called, you're out of luck.
    That's why this decorator exists. For example:

        # In views.py

        @transaction.atomic
        def do_something(request):
            transaction.on_commit(do_other_thing)
            return http.HttpResponse('yay!')


        # In test_something.py

        class MyTests(TestCase):

            @call_on_commit_immediately
            def test_something(self):
                self.client.get('/do/something')

    In this example, without the decorator, the `do_other_thing` function
    would simply never be called. This decorator fixes that but it doesn't
    guarantee, in tests, that it gets called correctly last after
    the transaction would have committed.
    """

    def run_immediately(some_callable):
        some_callable()

    @wraps(test_method)
    def inner(*args, **kwargs):
        with mock.patch("django.db.transaction.on_commit") as mocker:
            mocker.side_effect = run_immediately
            return test_method(*args, **kwargs)

    return inner
