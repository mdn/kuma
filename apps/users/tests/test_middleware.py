from django.contrib.auth.models import User

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr

from devmo.tests import LocalizingClient
from sumo.tests import TestCase
from users.models import UserBan


class BanTestCase(TestCase):
    fixtures = ['test_users.json']

    @attr('bans')
    def test_ban_middleware(self):
        """Ban middleware functions correctly."""
        client = LocalizingClient()
        client.login(username='testuser', password='testpass')

        resp = client.get('/')
        self.assertTemplateNotUsed(resp, 'users/user_banned.html')

        admin = User.objects.get(username='admin')
        testuser = User.objects.get(username='testuser')
        ban = UserBan(user=testuser, by=admin,
                      reason='Banned by unit test.',
                      is_active=True)
        ban.save()

        resp = client.get('/')
        self.assertTemplateUsed(resp, 'users/user_banned.html')
