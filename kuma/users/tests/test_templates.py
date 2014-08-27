from nose.tools import eq_, ok_
import test_utils

from django.contrib.auth.models import User

from sumo.urlresolvers import reverse
from devmo.tests import LocalizingClient
from .test_views import TESTUSER_PASSWORD


class AccountEmailTests(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.client = LocalizingClient()

    def test_account_email_page_requires_signin(self):
        url = reverse('account_email')
        r = self.client.get(url, follow=True)

        eq_(200, r.status_code)
        ok_(len(r.redirect_chain) > 0)
        ok_('Please sign in' in r.content)

    def test_account_email_page(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        url = reverse('account_email')
        r = self.client.get(url)
        test_strings = ['Make Primary', 'Re-send Verification', 'Remove',
                        'Add Email', 'Edit profile']

        eq_(200, r.status_code)
        for test_string in test_strings:
            ok_(test_string in r.content)


class SocialAccountConnectionsTests(test_utils.TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.client = LocalizingClient()

    def test_account_connections_page_requires_signin(self):
        url = reverse('socialaccount_connections')
        r = self.client.get(url, follow=True)

        eq_(200, r.status_code)
        ok_(len(r.redirect_chain) > 0)
        ok_('Please sign in' in r.content)

    def test_account_connections_page(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        url = reverse('socialaccount_connections')
        r = self.client.get(url)
        test_strings = ['Disconnect', 'Connect a new account', 'Edit profile']

        eq_(200, r.status_code)
        for test_string in test_strings:
            ok_(test_string in r.content,
                msg="Expected %s in content" % test_string)
