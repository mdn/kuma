from django.contrib.auth.models import User

from nose.tools import eq_

from sumo.tests import TestCase
from users.tests import profile


class ProfileTestCase(TestCase):
    fixtures = ['test_users.json']

    def test_user_get_profile(self):
        """user.get_profile() returns what you'd expect."""
        user = User.objects.all()[0]
        p = profile(user)

        eq_(p, user.get_profile())
