from os.path import dirname

import mock

from django.conf import settings, UserSettingsHolder
from django.contrib.auth.models import User
from django.utils.functional import wraps

import constance.config
from constance.backends import database as constance_database

import test_utils
from nose.plugins.skip import SkipTest

from devmo.models import UserProfile


def create_profile():
    """Create a user and a profile for a test account"""
    user = User.objects.create_user('tester23', 'tester23@example.com',
                                    'trustno1')

    profile = UserProfile()
    profile.user = user
    profile.fullname = "Tester Twentythree"
    profile.title = "Spaceship Pilot"
    profile.organization = "UFO"
    profile.location = "Outer Space"
    profile.bio = "I am a freaky space alien."
    profile.irc_nickname = "ircuser"
    profile.locale = 'en-US'
    profile.timezone = 'US/Central'
    profile.save()

    return (user, profile)


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
