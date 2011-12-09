import hashlib
from time import time

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core import mail
from django.utils.http import int_to_base36

import mock
from nose.tools import eq_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
from test_utils import RequestFactory

from dekicompat.tests import (MULTI_ACCOUNT_FIXTURE_XML,
                              SINGLE_ACCOUNT_FIXTURE_XML,
                              mock_post_mindtouch_user,
                              mock_put_mindtouch_user,
                              mock_get_deki_user_by_email,
                              mock_get_deki_user)

from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.tests import post
from users.models import RegistrationProfile
from users.tests import TestCaseBase
from users.views import _clean_next_url


class LoginTests(TestCaseBase):
    """Login tests."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(LoginTests, self).setUp()
        self.orig_debug = settings.DEBUG
        settings.DEBUG = True

    def tearDown(self):
        super(LoginTests, self).tearDown()
        settings.DEBUG = self.orig_debug

    def test_login_bad_password(self):
        '''Test login with a good username and bad password.'''
        response = post(self.client, 'users.login',
                        {'username': 'testuser', 'password': 'foobar'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Please enter a correct username and password. Note that both '
            'fields are case-sensitive.', doc('ul.errorlist li').text())

    def test_login_bad_username(self):
        '''Test login with a bad username.'''
        response = post(self.client, 'users.login',
                        {'username': 'foobarbizbin', 'password': 'testpass'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Please enter a correct username and password. Note that both '
            'fields are case-sensitive.', doc('ul.errorlist li').text())

    def test_login(self):
        '''Test a valid login.'''
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': 'testpass'})
        eq_(302, response.status_code)
        eq_('http://testserver' +
                reverse('home', locale=settings.LANGUAGE_CODE),
            response['location'])

    def test_login_next_parameter(self):
        '''Test with a valid ?next=url parameter.'''
        next = '/kb/new'

        # Verify that next parameter is set in form hidden field.
        response = self.client.get(urlparams(reverse('users.login'),
                                             next=next))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(next, doc('input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': 'testpass',
                                     'next': next})
        eq_(302, response.status_code)
        eq_('http://testserver' + next, response['location'])

    @mock.patch_object(Site.objects, 'get_current')
    def test_clean_url(self, get_current):
        '''Verify that protocol and domain get removed.'''
        get_current.return_value.domain = 'su.mo.com'
        r = RequestFactory().post('/users/login',
                                  {'next': 'https://su.mo.com/kb/new?f=b'})
        eq_('/kb/new?f=b', _clean_next_url(r))
        r = RequestFactory().post('/users/login',
                                  {'next': 'http://su.mo.com/kb/new'})
        eq_('/kb/new', _clean_next_url(r))

    @mock.patch_object(Site.objects, 'get_current')
    def test_login_invalid_next_parameter(self, get_current):
        '''Test with an invalid ?next=http://example.com parameter.'''
        get_current.return_value.domain = 'testserver.com'
        invalid_next = 'http://foobar.com/evil/'
        valid_next = reverse('home', locale=settings.LANGUAGE_CODE)

        # Verify that _valid_ next parameter is set in form hidden field.
        response = self.client.get(urlparams(reverse('users.login'),
                                             next=invalid_next))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(valid_next, doc('input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': 'testpass',
                                     'next': invalid_next})
        eq_(302, response.status_code)
        eq_('http://testserver' + valid_next, response['location'])

    def test_login_legacy_password(self):
        '''Test logging in with a legacy md5 password.'''
        legacypw = 'legacypass'

        # Set the user's password to an md5
        user = User.objects.get(username='testuser')
        user.password = hashlib.md5(legacypw).hexdigest()
        user.save()

        # Log in and verify that it's updated to a SHA-256
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': legacypw})
        eq_(302, response.status_code)
        user = User.objects.get(username='testuser')
        assert user.password.startswith('sha256$')

        # Try to log in again.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': legacypw})
        eq_(302, response.status_code)


class PasswordReset(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(PasswordReset, self).setUp()
        self.user = User.objects.get(username='testuser')
        self.user.email = 'valid@email.com'
        self.user.save()
        self.uidb36 = int_to_base36(self.user.id)
        self.token = default_token_generator.make_token(self.user)
        self.orig_debug = settings.DEBUG
        settings.DEBUG = True

    def tearDown(self):
        super(PasswordReset, self).tearDown()
        settings.DEBUG = self.orig_debug

    def test_bad_email(self):
        r = self.client.post(reverse('users.pw_reset'),
                             {'email': 'foo@bar.com'})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(0, len(mail.outbox))

    @mock.patch_object(Site.objects, 'get_current')
    def test_success(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        r = self.client.post(reverse('users.pw_reset'),
                             {'email': self.user.email})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Password reset') == 0
        assert mail.outbox[0].body.find('pwreset/%s' % self.uidb36) > 0

    @mock_get_deki_user
    @mock_get_deki_user_by_email
    @mock.patch_object(Site.objects, 'get_current')
    def test_deki_only_user(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        self.assertRaises(User.DoesNotExist, User.objects.get, username='testaccount')

        r = self.client.post(reverse('users.pw_reset'),
                             {'email': 'testaccount+update3@testaccount.com'})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Password reset') == 0

        u = User.objects.get(username='testaccount')
        assert mail.outbox[0].body.find('pwreset/%s' % int_to_base36(u.id)) > 0

    @mock.patch_object(Site.objects, 'get_current')
    def test_deki_email_multi_user(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        self.assertRaises(User.DoesNotExist, User.objects.get, username='testaccount')

        r = self.client.post(reverse('users.pw_reset'),
                             {'email': 'f487e0b2f7b637e4e7d5dd0ff76b0447@mozilla.com'})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Password reset') == 0

        u = User.objects.get(username='Ibn el haithem')
        assert mail.outbox[0].body.find('pwreset/%s' % int_to_base36(u.id)) > 0

    test_deki_email_multi_user = mock_get_deki_user(
        test_deki_email_multi_user,
        fixture_file=SINGLE_ACCOUNT_FIXTURE_XML)

    def _get_reset_url(self):
        return reverse('users.pw_reset_confirm',
                       args=[self.uidb36, self.token])

    def test_bad_reset_url(self):
        r = self.client.get('/users/pwreset/junk/', follow=True)
        eq_(r.status_code, 404)

        r = self.client.get(reverse('users.pw_reset_confirm',
                                    args=[self.uidb36, '12-345']))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Password reset unsuccessful', doc('article h1').text())

    def test_reset_fail(self):
        url = self._get_reset_url()
        r = self.client.post(url, {'new_password1': '', 'new_password2': ''})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc('ul.errorlist')))

        r = self.client.post(url, {'new_password1': 'one',
                                   'new_password2': 'two'})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_("The two password fields didn't match.",
            doc('ul.errorlist li').text())

    def test_reset_success(self):
        url = self._get_reset_url()
        new_pw = 'fjdka387fvstrongpassword!'
        assert self.user.check_password(new_pw) is False

        r = self.client.post(url, {'new_password1': new_pw,
                               'new_password2': new_pw})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetcomplete', r['location'])
        self.user = User.objects.get(username='testuser')
        assert self.user.check_password(new_pw)


class PasswordChangeTests(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(PasswordChangeTests, self).setUp()
        self.user = User.objects.get(username='testuser')
        self.url = reverse('users.pw_change')
        self.new_pw = 'fjdka387fvstrongpassword!'
        self.client.login(username='testuser', password='testpass')

    def test_change_password(self):
        assert self.user.check_password(self.new_pw) is False

        r = self.client.post(self.url, {'old_password': 'testpass',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwchangecomplete', r['location'])
        self.user = User.objects.get(username='testuser')
        assert self.user.check_password(self.new_pw)

    def test_bad_old_password(self):
        r = self.client.post(self.url, {'old_password': 'testpqss',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Your old password was entered incorrectly. Please enter it '
            'again.', doc('ul.errorlist').text())

    def test_new_pw_doesnt_match(self):
        r = self.client.post(self.url, {'old_password': 'testpqss',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw + '1'})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_("Your old password was entered incorrectly. Please enter it "
            "again. The two password fields didn't match.",
            doc('ul.errorlist').text())


class ResendConfirmationTests(TestCaseBase):

    @mock_post_mindtouch_user
    @mock_put_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_resend_confirmation(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        now = time()
        username = 'temp%s' % now

        RegistrationProfile.objects.create_inactive_user(
            username, 'testpass', 'testuser@email.com')
        eq_(1, len(mail.outbox))

        r = self.client.post(reverse('users.resend_confirmation'),
                             {'email': 'testuser@email.com'})
        eq_(200, r.status_code)
        eq_(2, len(mail.outbox))
        assert mail.outbox[1].subject.find('Please confirm your email') == 0
