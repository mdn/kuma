from django.contrib.auth.models import User

from nose.tools import eq_

from sumo.tests import TestCase
from users.helpers import profile_url, profile_avatar


class HelperTestCase(TestCase):
    def test_profile_url(self):
        user = User.objects.create(pk=500000, username=u'testuser')
        eq_(u'/tiki-user_information.php?locale=en-US&userId=500000',
            profile_url(user))

    def test_profile_avatar(self):
        user = User.objects.create(pk=500001, username=u'testuser2')
        eq_(u'/tiki-show_user_avatar.php?user=testuser2',
            profile_avatar(user))
