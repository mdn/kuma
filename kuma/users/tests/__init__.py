import random
from string import letters

from django.contrib.auth.models import User

from devmo.tests import LocalizingClient
from sumo.tests import TestCase

from ..models import UserProfile


class TestCaseBase(TestCase):
    """Base TestCase for the users app test cases."""

    def setUp(self):
        super(TestCaseBase, self).setUp()
        self.client = LocalizingClient()


def profile(user, **kwargs):
    """Return a saved profile for a given user."""
    p = UserProfile.objects.get(user=user)
    return p


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
