import hashlib

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core import mail
from django.utils.http import int_to_base36

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from test_utils import RequestFactory

from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.tests import post
from users.tests import TestCaseBase
from users.views import _clean_next_url


class LoginTests(TestCaseBase):
    """Login tests."""
    fixtures = ['users.json']

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
                        {'username': 'rrosario', 'password': 'foobar'})
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
                                    {'username': 'rrosario',
                                     'password': 'testpass'})
        eq_(302, response.status_code)
        eq_('http://testserver' + settings.LOGIN_REDIRECT_URL,
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
                                    {'username': 'rrosario',
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
        valid_next = settings.LOGIN_REDIRECT_URL

        # Verify that _valid_ next parameter is set in form hidden field.
        response = self.client.get(urlparams(reverse('users.login'),
                                             next=invalid_next))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(valid_next, doc('input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': 'testpass',
                                     'next': invalid_next})
        eq_(302, response.status_code)
        eq_('http://testserver' + valid_next, response['location'])

    def test_login_legacy_password(self):
        '''Test logging in with a legacy md5 password.'''
        legacypw = 'legacypass'

        # Set the user's password to an md5
        user = User.objects.get(username='rrosario')
        user.password = hashlib.md5(legacypw).hexdigest()
        user.save()

        # Log in and verify that it's updated to a SHA-256
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': legacypw})
        eq_(302, response.status_code)
        user = User.objects.get(username='rrosario')
        assert user.password.startswith('sha256$')

        # Try to log in again.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': legacypw})
        eq_(302, response.status_code)


class PasswordReset(TestCaseBase):
    fixtures = ['users.json']

    def setUp(self):
        super(PasswordReset, self).setUp()
        self.user = User.objects.get(username='rrosario')
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
        eq_(200, r.status_code)
        eq_(len(mail.outbox), 0)

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
        self.user = User.objects.get(username='rrosario')
        assert self.user.check_password(new_pw)


class EditProfileTests(TestCaseBase):
    fixtures = ['users.json']

    def test_edit_profile(self):
        url = reverse('users.edit_profile')
        self.client.login(username='rrosario', password='testpass')
        data = {'name': 'John Doe',
                'public_email': True,
                'bio': 'my bio',
                'website': 'http://google.com/',
                'twitter': '',
                'facebook': '',
                'irc_handle': 'johndoe',
                'timezone': 'America/New_York',
                'country': 'US',
                'city': 'Disney World'}
        r = self.client.post(url, data)
        eq_(302, r.status_code)
        profile = User.objects.get(username='rrosario').get_profile()
        for key in data:
            if key != 'timezone':
                eq_(data[key], getattr(profile, key))
        eq_(data['timezone'], profile.timezone.zone)
