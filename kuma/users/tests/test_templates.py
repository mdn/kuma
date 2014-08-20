import mock
from nose.tools import eq_, ok_

from django.contrib.auth.models import User

from sumo.urlresolvers import reverse
from sumo.tests import TestCase
from .test_views import TESTUSER_PASSWORD
from . import verify_strings_in_response, TestCaseBase


# TODO: Figure out why TestCaseBase doesn't work here
class SignupTests(TestCase):
    fixtures = ['test_users.json']

    @mock.patch('requests.post')
    def test_signup_page(self, mock_post):
        user_email = "newuser@test.com"
        mock_post.return_value = mock_resp = mock.Mock()
        mock_resp.json.return_value={
            "status": "okay",
            "email": user_email,
            "audience": "https://developer-local.allizom.org"
        }

        url = reverse('persona_login')
        r = self.client.post(url, follow=True)

        eq_(200, r.status_code)
        ok_('Sign In Failure' not in r.content)
        test_strings = ['Create your MDN profile to continue', 'choose a username',
                        'having trouble']
        verify_strings_in_response(test_strings, r)


class AccountEmailTests(TestCaseBase):

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
        eq_(200, r.status_code)

        test_strings = ['Make Primary', 'Re-send Confirmation', 'Remove',
                        'Add Email', 'Edit profile']
        verify_strings_in_response(test_strings, r)


class SocialAccountConnectionsTests(TestCaseBase):

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
        test_strings = ['Disconnect', 'Connect a new account', 'Edit profile',
                        'Connect with']

        eq_(200, r.status_code)
        verify_strings_in_response(test_strings, r)
