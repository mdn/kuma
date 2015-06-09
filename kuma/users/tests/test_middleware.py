from nose.plugins.attrib import attr

from . import UserTestCase
from ..models import UserBan


class BanTestCase(UserTestCase):
    localizing_client = True

    @attr('bans')
    def test_ban_middleware(self):
        """Ban middleware functions correctly."""
        self.client.login(username='testuser', password='testpass')

        resp = self.client.get('/')
        self.assertTemplateNotUsed(resp, 'users/user_banned.html')

        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')
        ban = UserBan(user=testuser, by=admin,
                      reason='Banned by unit test.',
                      is_active=True)
        ban.save()

        resp = self.client.get('/')
        self.assertTemplateUsed(resp, 'users/user_banned.html')
