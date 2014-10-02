from nose.tools import ok_

from django.contrib.auth.models import User

from devmo.tests import KumaTestCase

from ..models import UserProfile


class UserTestCase(KumaTestCase):
    """Base TestCase for the users app test cases."""
    fixtures = ['test_users.json']


def profile(user, **kwargs):
    """Return a saved profile for a given user."""
    p = UserProfile.objects.get(user=user)
    return p


def user(save=False, **kwargs):
    if 'username' not in kwargs:
        kwargs['username'] = User.objects.make_random_password(length=15)
    password = kwargs.pop('password', 'password')
    user = User(**kwargs)
    user.set_password(password)
    if save:
        user.save()
    return user


def verify_strings_in_response(test_strings, response):
    for test_string in test_strings:
        ok_(test_string in response.content,
            msg="Expected '%s' in content." % test_string)


def verify_strings_not_in_response(test_strings, response):
    for test_string in test_strings:
        ok_(test_string not in response.content,
            msg="Found unexpected '%s' in content." % test_string)
