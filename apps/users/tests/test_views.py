from time import time
import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from dekicompat.tests import (mock_mindtouch_login,
                              mock_missing_get_deki_user,
                              mock_get_deki_user,
                              mock_get_deki_user_by_email,
                              mock_missing_get_deki_user_by_email,
                              mock_put_mindtouch_user,
                              mock_post_mindtouch_user)

from dekicompat.backends import DekiUserBackend, MINDTOUCH_USER_XML
from notifications.tests import watch
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.models import RegistrationProfile, EmailChange
from users.views import SESSION_VERIFIED_EMAIL
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
        self.assertRaises(User.DoesNotExist, User.objects.get,
                          username='nouser')

        response = self.client.post(reverse('users.login'),
                                    {'username': 'nouser',
                                     'password': 'nopass'}, follow=True)
        eq_(200, response.status_code)
        self.assertContains(response, 'Please enter a correct username and '
                                      'password.')

    @mock.patch_object(Site.objects, 'get_current')
    def test_django_login(self, get_current):
        get_current.return_value.domain = 'dev.mo.org'

        response = self.client.post(reverse('users.login'),
                                    {'username': 'testuser',
                                     'password': 'testpass'}, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('testuser', doc.find('ul.user-state a:first').text())

    @mock_mindtouch_login
    @mock_get_deki_user
    @mock_put_mindtouch_user
    @mock.patch_object(Site.objects, 'get_current')
    def test_mindtouch_creds_create_user_and_profile(self, get_current):
        get_current.return_value.domain = 'dev.mo.org'

        if not getattr(settings, 'DEKIWIKI_MOCK', False):
            # HACK: Ensure that expected user details are in MindTouch when not
            # mocking the API
            mt_email = 'testaccount+update3@testaccount.com'
            user_xml = MINDTOUCH_USER_XML % dict(username="testaccount",
                    email=mt_email, fullname="None", status="active",
                    language="", timezone="-08:00", role="Contributor")
            DekiUserBackend.put_mindtouch_user(deki_user_id='=testaccount',
                                               user_xml=user_xml)
            passwd_url = '%s/@api/deki/users/%s/password?apikey=%s' % (
                settings.DEKIWIKI_ENDPOINT, '=testaccount',
                settings.DEKIWIKI_APIKEY)
            requests.put(passwd_url, data='theplanet')

        self.assertRaises(User.DoesNotExist, User.objects.get,
                          username='testaccount')

        # Try to log in as a MindTouch user
        response = self.client.post(reverse('users.login'),
                                    {'username': 'testaccount',
                                     'password': 'theplanet'}, follow=True)
        eq_(200, response.status_code)

        # Ensure there are no validation errors
        page = pq(response.content)
        eq_(0, page.find('.errorlist').length,
            "There should be no validation errors in login")

        # Login should have auto-created django user
        u = User.objects.get(username='testaccount')
        eq_(True, u.is_active)
        ok_(u.get_profile())

        # Login page should show welcome back
        doc = pq(response.content)
        eq_('testaccount', doc.find('ul.user-state a:first').text())


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
            eq_('testuser01+changed@test.com',
                doc('user').find('email').text())

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


class BrowserIDTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        # Ensure @ssl_required goes unenforced.
        settings.DEBUG = True
        # Set up some easily-testable redirects.
        settings.LOGIN_REDIRECT_URL = 'SUCCESS'
        settings.LOGIN_REDIRECT_URL_FAILURE = 'FAILURE'
        # BrowserID will squawk if this isn't set
        settings.SITE_URL = 'http://testserver'
        self.client = LocalizingClient()

    def test_invalid_post(self):
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'))
        eq_(302, resp.status_code)
        ok_('FAILURE' in resp['Location'])

    @mock.patch('users.views._verify_browserid')
    def test_invalid_assertion(self, _verify_browserid):
        _verify_browserid.return_value = None

        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'bad data'})
        eq_(302, resp.status_code)
        ok_('FAILURE' in resp['Location'])

    @mock_get_deki_user_by_email
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock.patch('users.views._verify_browserid')
    def test_valid_assertion_with_django_user(self, _verify_browserid):
        _verify_browserid.return_value = {'email': 'testuser2@test.com'}

        # Posting the fake assertion to browserid_verify should work, with the
        # actual verification method mocked out.
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)
        ok_('SUCCESS' in resp['Location'])

        # The session should look logged in, now.
        ok_('_auth_user_id' in self.client.session.keys())
        eq_('django_browserid.auth.BrowserIDBackend',
            self.client.session.get('_auth_user_backend', ''))

    @mock_get_deki_user_by_email
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock.patch('users.views._verify_browserid')
    def test_explain_popup(self, _verify_browserid):
        _verify_browserid.return_value = {'email': 'testuser2@test.com'}
        resp = self.client.get(reverse('home', locale='en-US'))
        doc = pq(resp.content)
        eq_(True, 'toggle' in doc.find('li#user-signin').html())

        # Posting the fake assertion to browserid_verify should work, with the
        # actual verification method mocked out.
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_('1', resp.cookies.get('browserid_explained').value)

        resp = self.client.get(reverse('users.logout'), locale='en-US')

        # even after logout, cookie should prevent the toggle
        resp = self.client.get(reverse('home', locale='en-US'))
        eq_('1', self.client.cookies.get('browserid_explained').value)
        doc = pq(resp.content)
        eq_(False, 'toggle' in doc.find('li#user-signin').html())

    @mock_get_deki_user_by_email
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock.patch('users.views._verify_browserid')
    def test_valid_assertion_with_mindtouch_user(self, _verify_browserid):
        mt_email = 'testaccount@testaccount.com'
        _verify_browserid.return_value = {'email': mt_email}

        # Probably overkill but let's be sure we're testing the right thing.
        try:
            User.objects.get(email=mt_email)
            ok_(False, "The MindTouch user shouldn't exist in Django yet.")
        except User.DoesNotExist:
            pass

        if not getattr(settings, 'DEKIWIKI_MOCK', False):
            # HACK: Ensure that expected user details are in MindTouch when not
            # mocking the API
            user_xml = MINDTOUCH_USER_XML % dict(username="testaccount",
                    email=mt_email, fullname="None", status="active",
                    language="", timezone="-08:00", role="Contributor")
            DekiUserBackend.put_mindtouch_user(deki_user_id='=testaccount',
                                               user_xml=user_xml)

        deki_user = DekiUserBackend.get_deki_user_by_email(mt_email)
        ok_(deki_user is not None, "The MindTouch user should exist")

        # Posting the fake assertion to browserid_verify should work, with the
        # actual verification method mocked out.
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)
        ok_('SUCCESS' in resp['Location'])

        # The session should look logged in, now.
        ok_('_auth_user_id' in self.client.session.keys())
        eq_('django_browserid.auth.BrowserIDBackend',
            self.client.session.get('_auth_user_backend', ''))

        # And, after all the above, there should be a Django user now.
        try:
            User.objects.get(email=mt_email)
        except User.DoesNotExist:
            ok_(False, "The MindTouch user should exist in Django now.")

    @mock_missing_get_deki_user_by_email
    @mock_missing_get_deki_user
    @mock_post_mindtouch_user
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock.patch('users.views._verify_browserid')
    def test_valid_assertion_with_new_account_creation(self,
                                                       _verify_browserid):
        new_username = 'neverbefore'
        new_email = 'never.before.seen@example.com'
        _verify_browserid.return_value = {'email': new_email}

        try:
            user = User.objects.get(email=new_email)
            ok_(False, "User for email should not yet exist")
        except User.DoesNotExist:
            pass

        if not getattr(settings, 'DEKIWIKI_MOCK', False):
            # HACK: When not mocking the MindTouch API, ensure that there's no
            # leftover user with the same name & email as what we want to
            # register
            import random
            rand_num = random.randint(0, 1000000)
            user_xml = MINDTOUCH_USER_XML % dict(
                    username="%s_%s" % (new_username, rand_num),
                    email="%s_%s" % (rand_num, new_email),
                    fullname="", status="inactive",
                    language="", timezone="-08:00",
                    role="Contributor")
            DekiUserBackend.put_mindtouch_user(
                    deki_user_id='=%s' % new_username, user_xml=user_xml)

        # Sign in with a verified email, but with no existing account
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)

        # This should be a redirect to the BrowserID registration page.
        redir_url = resp['Location']
        reg_url = reverse('users.browserid_register', locale='en-US')
        ok_(reg_url in redir_url)

        # And, as part of the redirect, the verified email address should be in
        # our session now.
        ok_(SESSION_VERIFIED_EMAIL in self.client.session.keys())
        verified_email = self.client.session[SESSION_VERIFIED_EMAIL]
        eq_(new_email, verified_email)

        # Grab the redirect, assert that there's a create_user form present
        resp = self.client.get(redir_url)
        page = pq(resp.content)
        form = page.find('form#create_user')
        eq_(1, form.length)

        # There should be no error lists on first load
        eq_(0, page.find('.errorlist').length)

        # Submit the create_user form, with a chosen username
        resp = self.client.post(redir_url, {'username': 'neverbefore',
                                            'action': 'register'})

        # The submission should result in a redirect to the new user's profile
        eq_(302, resp.status_code)
        redir_url = resp['Location']
        profile_url = reverse('devmo_profile_view', args=[new_username])
        ok_(profile_url in redir_url)

        # The session should look logged in, now.
        ok_('_auth_user_id' in self.client.session.keys())
        eq_('django_browserid.auth.BrowserIDBackend',
            self.client.session.get('_auth_user_backend', ''))

        # Ensure that the user was created, and with the submitted username and
        # verified email address
        try:
            user = User.objects.get(email=new_email)
            eq_(new_username, user.username)
            eq_(new_email, user.email)
        except User.DoesNotExist:
            ok_(False, "New user should have been created")

    @mock_missing_get_deki_user_by_email
    @mock_post_mindtouch_user
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock_get_deki_user
    @mock.patch('users.views._verify_browserid')
    def test_valid_assertion_with_existing_account_login(self,
                                                         _verify_browserid):
        new_email = 'mynewemail@example.com'
        _verify_browserid.return_value = {'email': new_email}

        try:
            User.objects.get(email=new_email)
            ok_(False, "User for email should not yet exist")
        except User.DoesNotExist:
            pass

        # Sign in with a verified email, but with no existing account
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)

        # This should be a redirect to the BrowserID registration page.
        redir_url = resp['Location']
        reg_url = reverse('users.browserid_register', locale='en-US')
        ok_(reg_url in redir_url)

        # And, as part of the redirect, the verified email address should be in
        # our session now.
        ok_(SESSION_VERIFIED_EMAIL in self.client.session.keys())
        verified_email = self.client.session[SESSION_VERIFIED_EMAIL]
        eq_(new_email, verified_email)

        # Grab the redirect, assert that there's a create_user form present
        resp = self.client.get(redir_url)
        page = pq(resp.content)
        form = page.find('form#existing_user')
        eq_(1, form.length)

        # There should be no error lists on first load
        eq_(0, page.find('.errorlist').length)

        # Submit the existing_user form, with a chosen username
        resp = self.client.post(redir_url, {'username': 'testuser',
                                            'password': 'testpass',
                                            'action': 'login'})

        # A successful login should result in a redirect to success.
        eq_(302, resp.status_code)
        ok_('SUCCESS' in resp['Location'])

        # The session should look logged in, now.
        ok_('_auth_user_id' in self.client.session.keys())

        # And, after all the above, there should be a Django user now.
        try:
            User.objects.get(email=new_email)
        except User.DoesNotExist:
            ok_(False, "The MindTouch user should exist in Django now.")

    @mock_get_deki_user_by_email
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock.patch('users.views._verify_browserid')
    def test_valid_assertion_changing_email(self, _verify_browserid):
        # just need to be authenticated, not necessarily BrowserID
        self.client.login(username='testuser', password='testpass')

        _verify_browserid.return_value = {'email': 'testuser+changed@test.com'}

        # posting a valid assertion to browserid_verify changes email
        # if the client is already logged-in
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)
        ok_('profiles/testuser/edit' in resp['Location'])

        resp = self.client.get(reverse('devmo_profile_edit', locale='en-US',
                                       args=['testuser', ]))
        eq_(200, resp.status_code)
        doc = pq(resp.content)
        ok_('testuser+changed@test.com' in doc.find('li#field_email').text())

    @mock_get_deki_user_by_email
    @mock_put_mindtouch_user
    @mock_mindtouch_login
    @mock.patch('users.views._verify_browserid')
    def test_valid_assertion_doesnt_steal_email(self, _verify_browserid):
        # just need to be authenticated, not necessarily BrowserID
        self.client.login(username='testuser', password='testpass')

        _verify_browserid.return_value = {'email': 'testuser2@test.com'}

        # posting a valid assertion to browserid_verify doesn't change email
        # if the new email already belongs to another user
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)
        ok_('change_email' in resp['Location'])

        resp = self.client.get(reverse('devmo_profile_edit', locale='en-US',
                                       args=['testuser', ]))
        eq_(200, resp.status_code)
        doc = pq(resp.content)
        ok_('testuser@test.com' in doc.find('li#field_email').text())
