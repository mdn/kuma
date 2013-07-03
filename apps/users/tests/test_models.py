# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.auth.models import User

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from sumo.tests import TestCase
from users.models import UserBan
from users.tests import profile


class ProfileTestCase(TestCase):
    fixtures = ['test_users.json']

    def test_user_get_profile(self):
        """user.get_profile() returns what you'd expect."""
        user = User.objects.all()[0]
        p = profile(user)

        eq_(p, user.get_profile())


class BanTestCase(TestCase):
    fixtures = ['test_users.json']

    @attr('bans')
    def test_ban_user(self):
        testuser = User.objects.get(username='testuser')
        admin = User.objects.get(username='admin')
        ok_(testuser.is_active)
        ban = UserBan(user=testuser,
                      by=admin,
                      reason='Banned by unit test')
        ban.save()
        testuser_banned = User.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        ban.is_active = False
        ban.save()
        testuser_unbanned = User.objects.get(username='testuser')
        ok_(testuser_unbanned.is_active)
