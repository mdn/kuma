from time import time
import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from dekicompat.tests import (mock_mindtouch_login,
                              mock_missing_get_deki_user,
                              mock_get_deki_user,
                              mock_put_mindtouch_user,
                              mock_post_mindtouch_user)

from dekicompat.backends import DekiUserBackend
from devmo.tests import mock_fetch_user_feed
from notifications.tests import watch
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.models import RegistrationProfile, EmailChange
from users.tests import get_deki_user_doc


class LoginTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client = LocalizingClient()
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    @mock.patch_object(Site.objects, 'get_current')
    def test_bad_login_fails_both_backends(self, get_current):
        get_current.return_value.domain = 'dev.mo.org'
        self.assertRaises(User.DoesNotExist, User.objects.get, username='nouser')

        response = self.client.post(reverse('users.login'),
                                    {'username': 'nouser',
                                     'password': 'nopass'}, follow=True)
        eq_(200, response.status_code)
        self.assertContains(response, 'Please enter a correct username and password.')

    @mock.patch_object(Site.objects, 'get_current')
    def test_django_login(self, get_current):
        get_current.return_value.domain = 'dev.mo.org'

        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': 'testpass'}, follow=True)
        eq_(200, response.status_code)
        self.assertContains(response, 'Welcome back, testuser')

    @mock_mindtouch_login
    @mock_get_deki_user
    @mock_put_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_mindtouch_creds_create_user_and_profile(self, get_current):
        get_current.return_value.domain = 'dev.mo.org'
        self.assertRaises(User.DoesNotExist, User.objects.get, username='testaccount')

        # Try to log in as a MindTouch user
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testaccount',
                                     'password': 'theplanet'}, follow=True)
        eq_(200, response.status_code)

        # Login should have auto-created django user
        u = User.objects.get(username='testaccount')
        eq_(True, u.is_active)
        ok_(u.get_profile())

        # Login page should show welcome back
        self.assertContains(response, 'Welcome back, testaccount')


class RegisterTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client = LocalizingClient()
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    @mock_missing_get_deki_user
    @mock_put_mindtouch_user
    @mock_post_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        now = time()
        username = 'newb%s' % now
        response = self.client.post(reverse('users.register'),
                                    {'username': username,
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username=username)
        assert u.password.startswith('sha256')
        assert not u.is_active
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        key = RegistrationProfile.objects.all()[0].activation_key
        assert mail.outbox[0].body.find('activate/%s' % key) > 0

        # Now try to log in
        u.is_active = True
        u.save()
        response = self.client.post(reverse('users.login'),
                                    {'username': username,
                                     'password': 'foo'}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/en-US/', response.redirect_chain[0][0])

    @mock_missing_get_deki_user
    @mock_put_mindtouch_user
    @mock_post_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user_posts_mindtouch_user(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        now = time()
        username = 'n00b%s' % now
        response = self.client.post(reverse('users.register'),
                                    {'username': username,
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username=username)
        assert u.password.startswith('sha256')
        assert not u.is_active
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        key = RegistrationProfile.objects.all()[0].activation_key
        assert mail.outbox[0].body.find('activate/%s' % key) > 0

        if not settings.DEKIWIKI_MOCK:
            deki_id = u.get_profile().deki_user_id
            doc = get_deki_user_doc(u)
            eq_(str(deki_id), doc('user').attr('id'))
            eq_(username, doc('username').text())

        # Now try to log in
        u.is_active = True
        u.save()
        response = self.client.post(reverse('users.login'),
                                    {'username': username,
                                     'password': 'foo'}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/en-US/', response.redirect_chain[0][0])

    @mock_missing_get_deki_user
    @mock_post_mindtouch_user
    @mock_put_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_unicode_password(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        now = time()
        username = 'cjk%s' % now
        u_str = u'\xe5\xe5\xee\xe9\xf8\xe7\u6709\u52b9'
        response = self.client.post(reverse('users.register', locale='ja'),
                                    {'username': username,
                                     'email': 'cjkuser@example.com',
                                     'password': u_str,
                                     'password2': u_str}, follow=True)
        eq_(200, response.status_code)
        u = User.objects.get(username=username)
        u.is_active = True
        u.save()
        assert u.password.startswith('sha256')

        # make sure you can login now
        response = self.client.post(reverse('users.login', locale='ja'),
                                    {'username': username,
                                     'password': u_str}, follow=True)
        eq_(200, response.status_code)
        eq_('http://testserver/ja/', response.redirect_chain[0][0])

    @mock_put_mindtouch_user
    @mock_post_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user_activation(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        now = time()
        username = 'sumo%s' % now
        user = RegistrationProfile.objects.create_inactive_user(
            username, 'testpass', 'sumouser@test.com')
        assert not user.is_active
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user = User.objects.get(pk=user.pk)
        assert user.is_active

    @mock_put_mindtouch_user
    @mock_post_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_new_user_claim_watches(self, get_current):
        """Claim user watches upon activation."""
        get_current.return_value.domain = 'su.mo.com'

        watch(email='sumouser@test.com', save=True)

        now = time()
        username = 'sumo%s' % now
        user = RegistrationProfile.objects.create_inactive_user(
            username, 'testpass', 'sumouser@test.com')
        key = RegistrationProfile.objects.all()[0].activation_key
        self.client.get(reverse('users.activate', args=[key]), follow=True)

        # Watches are claimed.
        assert user.watch_set.exists()

    @mock_get_deki_user
    def test_duplicate_username(self):
        response = self.client.post(reverse('users.register'),
                                    {'username': 'testuser',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    @mock_get_deki_user
    def test_duplicate_mindtouch_username(self):
        response = self.client.post(reverse('users.register'),
                                    {'username': 'testaccount',
                                     'email': 'testaccount@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    @mock_get_deki_user
    def test_duplicate_email(self):
        User.objects.create(username='noob', email='noob@example.com').save()
        response = self.client.post(reverse('users.register'),
                                    {'username': 'newbie',
                                     'email': 'noob@example.com',
                                     'password': 'foo',
                                     'password2': 'foo'}, follow=True)
        self.assertContains(response, 'already exists')

    @mock_get_deki_user
    def test_no_match_passwords(self):
        response = self.client.post(reverse('users.register'),
                                    {'username': 'newbie',
                                     'email': 'newbie@example.com',
                                     'password': 'foo',
                                     'password2': 'bar'}, follow=True)
        self.assertContains(response, 'must match')


class ChangeEmailTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.client = LocalizingClient()

    @mock.patch_object(Site.objects, 'get_current')
    def test_user_change_email(self, get_current):
        """Send email to change user's email and then change it."""
        get_current.return_value.domain = 'su.mo.com'

        self.client.login(username='testuser', password='testpass')
        # Attempt to change email.
        response = self.client.post(reverse('users.change_email'),
                                    {'email': 'paulc@trololololololo.com'},
                                    follow=True)
        eq_(200, response.status_code)

        # Be notified to click a confirmation link.
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]
        assert ec.activation_key in mail.outbox[0].body
        eq_('paulc@trololololololo.com', ec.email)

        # Visit confirmation link to change email.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        u = User.objects.get(username='testuser')
        eq_('paulc@trololololololo.com', u.email)

    @mock_get_deki_user
    @mock_put_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_user_change_email_updates_mindtouch(self, get_current):
        """Send email to change user's email and then change it."""
        get_current.return_value.domain = 'su.mo.com'

        self.client.login(username='testuser01', password='testpass')
        # Attempt to change email.
        response = self.client.post(reverse('users.change_email'),
                                    {'email': 'testuser01+changed@test.com'},
                                    follow=True)
        eq_(200, response.status_code)

        # Be notified to click a confirmation link.
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]
        assert ec.activation_key in mail.outbox[0].body
        eq_('testuser01+changed@test.com', ec.email)

        # Visit confirmation link to change email.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        u = User.objects.get(username='testuser01')
        eq_('testuser01+changed@test.com', u.email)

        if not settings.DEKIWIKI_MOCK:
            deki_id = u.get_profile().deki_user_id
            doc = get_deki_user_doc(u)
            eq_(str(deki_id), doc('user').attr('id'))
            eq_('testuser01+changed@test.com', doc('user').find('email').text())

    def test_user_change_email_same(self):
        """Changing to same email shows validation error."""
        self.client.login(username='testuser', password='testpass')
        user = User.objects.get(username='testuser')
        user.email = 'valid@email.com'
        user.save()
        response = self.client.post(reverse('users.change_email'),
                                    {'email': user.email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('This is your current email.', doc('ul.errorlist').text())

    def test_user_change_email_duplicate(self):
        """Changing to same email shows validation error."""
        self.client.login(username='testuser', password='testpass')
        email = 'testuser2@test.com'
        response = self.client.post(reverse('users.change_email'),
                                    {'email': email})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('A user with that email address already exists.',
            doc('ul.errorlist').text())

    @mock.patch_object(Site.objects, 'get_current')
    def test_user_confirm_email_duplicate(self, get_current):
        """If we detect a duplicate email when confirming an email change,
        don't change it and notify the user."""
        get_current.return_value.domain = 'su.mo.com'
        self.client.login(username='testuser', password='testpass')
        old_email = User.objects.get(username='testuser').email
        new_email = 'newvalid@email.com'
        response = self.client.post(reverse('users.change_email'),
                                    {'email': new_email})
        eq_(200, response.status_code)
        assert mail.outbox[0].subject.find('Please confirm your') == 0
        ec = EmailChange.objects.all()[0]

        # Before new email is confirmed, give the same email to a user
        other_user = User.objects.filter(username='testuser2')[0]
        other_user.email = new_email
        other_user.save()

        # Visit confirmation link and verify email wasn't changed.
        response = self.client.get(reverse('users.confirm_email',
                                           args=[ec.activation_key]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Unable to change email for user testuser',
            doc('.main h1').text())
        u = User.objects.get(username='testuser')
        eq_(old_email, u.email)
