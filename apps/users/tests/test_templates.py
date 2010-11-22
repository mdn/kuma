import hashlib

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.tests import post
from users.tests import TestCaseBase


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
