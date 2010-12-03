from django.conf import settings
from django.contrib.auth.models import User

from nose.tools import eq_

from sumo.tests import TestCase
from users.helpers import profile_url, profile_avatar
from users.models import Profile


class HelperTestCase(TestCase):
    def test_profile_url(self):
        user = User.objects.create(pk=500000, username=u'testuser')
        eq_(u'/tiki-user_information.php?locale=en-US&userId=500000',
            profile_url(user))

    def test_profile_avatar_default(self):
        user = User.objects.create(pk=500000, username=u'testuser')
        profile = Profile.objects.create(user=user)
        eq_(settings.DEFAULT_AVATAR, profile_avatar(user))

    def test_profile_avatar(self):
        user = User.objects.create(pk=500000, username=u'testuser')
        profile = Profile(user=user)
        profile.avatar = 'images/foo.png'
        profile.save()
        eq_('%simages/foo.png' % settings.MEDIA_URL, profile_avatar(user))
