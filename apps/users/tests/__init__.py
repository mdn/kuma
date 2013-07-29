import random
from string import letters
import requests

from nose.tools import eq_
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.auth.models import User

from devmo.models import UserProfile
from sumo.tests import LocalizingClient, TestCase


class TestCaseBase(TestCase):
    """Base TestCase for the users app test cases."""

    def setUp(self):
        super(TestCaseBase, self).setUp()
        self.client = LocalizingClient()


def profile(user, **kwargs):
    """Return a saved profile for a given user."""
    p = UserProfile.objects.get(user=user)
    return p


def user(save=False, **kwargs):
    defaults = {'password':
                    'sha1$d0fcb$661bd5197214051ed4de6da4ecdabe17f5549c7c'}
    if 'username' not in kwargs:
        defaults['username'] = ''.join(random.choice(letters)
                                       for x in xrange(15))
    defaults.update(kwargs)
    u = User(**defaults)
    if save:
        u.save()
    return u
