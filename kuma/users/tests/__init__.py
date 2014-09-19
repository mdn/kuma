import random
from string import letters

from nose.tools import ok_

from django.contrib.auth.models import User

from devmo.tests import LocalizingClient
from sumo.tests import TestCase

from ..models import UserProfile


class TestCaseBase(TestCase):
    """Base TestCase for the users app test cases."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(TestCaseBase, self).setUp()
        self.client = LocalizingClient()


def profile(user, **kwargs):
    """Return a saved profile for a given user."""
    p = UserProfile.objects.get(user=user)
    return p


def user(save=False, **kwargs):
    defaults = {
        'password': 'sha1$d0fcb$661bd5197214051ed4de6da4ecdabe17f5549c7c'
    }
    if 'username' not in kwargs:
        defaults['username'] = ''.join(random.choice(letters)
                                       for x in xrange(15))
    defaults.update(kwargs)
    u = User(**defaults)
    if save:
        u.save()
    return u


def verify_strings_in_response(test_strings, response):
    for test_string in test_strings:
        ok_(test_string in response.content,
            msg="Expected '%s' in content." % test_string)


def verify_strings_not_in_response(test_strings, response):
    for test_string in test_strings:
        ok_(test_string not in response.content,
            msg="Found unexpected '%s' in content." % test_string)
