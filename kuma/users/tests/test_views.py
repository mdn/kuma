import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.test.utils import override_settings
from django.core.paginator import PageNotAnInteger

import mock
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
from test_utils import RequestFactory
from waffle.models import Switch

from devmo.tests import mock_lookup_user, LocalizingClient
from sumo.tests import TestCase
from sumo.urlresolvers import reverse

from ..models import UserProfile, UserBan
from ..views import (SESSION_VERIFIED_EMAIL, _clean_next_url,
                     WELCOME_EMAIL_STRINGS)
from . import create_profile

TESTUSER_PASSWORD = 'testpass'


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
    def test_clean_next_url_request_properties(self, get_current):
        '''_clean_next_url checks POST, GET, and REFERER'''
        get_current.return_value.domain = 'dev.mo.org'

        r = RequestFactory().get('/users/login', {'next': '/demos/submit'},
                                 HTTP_REFERER='referer-trumped-by-get')
        eq_('/demos/submit', _clean_next_url(r))
        r = RequestFactory().post('/users/login', {'next': '/demos/submit'})
        eq_('/demos/submit', _clean_next_url(r))
        r = RequestFactory().get('/users/login', HTTP_REFERER='/demos/submit')
        eq_('/demos/submit', _clean_next_url(r))

    @mock.patch_object(Site.objects, 'get_current')
    def test_clean_next_url_no_self_redirects(self, get_current):
        '''_clean_next_url checks POST, GET, and REFERER'''
        get_current.return_value.domain = 'dev.mo.org'

        for next in [settings.LOGIN_URL, settings.LOGOUT_URL]:
            r = RequestFactory().get('/users/login', {'next': next})
            eq_(None, _clean_next_url(r))

    @mock.patch_object(Site.objects, 'get_current')
    def test_clean_next_url_invalid_next_parameter(self, get_current):
        '''_clean_next_url cleans invalid urls'''
        get_current.return_value.domain = 'dev.mo.org'

        for next in self._invalid_nexts():
            r = RequestFactory().get('/users/login', {'next': next})
            eq_(None, _clean_next_url(r))

    def _invalid_nexts(self):
        return ['http://foobar.com/evil/', '//goo.gl/y-bad']


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

        # TODO: upgrade mock to 0.8.0 so we can do this.
        """
        self.lookup = mock.patch('basket.lookup_user')
        self.subscribe = mock.patch('basket.subscribe')
        self.unsubscribe = mock.patch('basket.unsubscribe')

        self.lookup.return_value = mock_lookup_user()
        self.subscribe.return_value = True
        self.unsubscribe.return_value = True

        self.lookup.start()
        self.subscribe.start()
        self.unsubscribe.start()

    def tearDown(self):
        self.lookup.stop()
        self.subscribe.stop()
        self.unsubscribe.stop()
        """

    def test_invalid_post(self):
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'))
        eq_(302, resp.status_code)
        ok_('FAILURE' in resp['Location'])

    @mock.patch('kuma.users.views._verify_browserid')
    def test_invalid_assertion(self, _verify_browserid):
        _verify_browserid.return_value = None

        resp = self.client.post(reverse('users.browserid_verify',
                                        locale='en-US'),
                                {'assertion': 'bad data'})
        eq_(302, resp.status_code)
        ok_('FAILURE' in resp['Location'])

    @mock.patch('kuma.users.views._verify_browserid')
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

    @mock.patch('kuma.users.views._verify_browserid')
    def test_explain_popup(self, _verify_browserid):
        _verify_browserid.return_value = {'email': 'testuser2@test.com'}
        resp = self.client.get(reverse('home', locale='en-US'))

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


    def _signin_new_email(self, locale, new_email):
        # Sign in with a verified email, but with no existing account
        resp = self.client.post(reverse('users.browserid_verify',
                                        locale=locale),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)

        # This should be a redirect to the BrowserID registration page.
        redir_url = resp['Location']
        reg_url = reverse('users.browserid_register', locale=locale)
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

        return redir_url


    def _register_user(self, register_url, new_username, new_email):
        # Submit the create_user form, with a chosen username
        resp = self.client.post(register_url, {'username': new_username,
                                            'action': 'register',
                                            'country': 'us',
                                            'format': 'html'})

        # The submission should result in a redirect to the session's redirect
        # value
        eq_(302, resp.status_code)
        redir_url = resp['Location']
        ok_('SUCCESS' in redir_url)

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


    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    @mock.patch('kuma.users.views._verify_browserid')
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_valid_assertion_with_new_account_creation(self,
                                                       _verify_browserid,
                                                       unsubscribe,
                                                       subscribe,
                                                       lookup_user):
        new_email = 'never.before.seen@example.com'
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        _verify_browserid.return_value = {'email': new_email}

        new_username = 'neverbefore'

        try:
            User.objects.get(email=new_email)
            ok_(False, "User for email should not yet exist")
        except User.DoesNotExist:
            pass

        register_url = self._signin_new_email('en-US', new_email)

        self._register_user(register_url, new_username, new_email)


    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    @mock.patch('kuma.users.views._verify_browserid')
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_new_account_email(self,
                               _verify_browserid,
                               unsubscribe,
                               subscribe,
                               lookup_user
                              ):
        new_email = 'never.before.seen@example.com'
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        _verify_browserid.return_value = {'email': new_email}

        Switch.objects.create(name='welcome_email', active=True)
        new_username = 'neverbefore'

        try:
            User.objects.get(email=new_email)
            ok_(False, "User for email should not yet exist")
        except User.DoesNotExist:
            pass

        register_url = self._signin_new_email('en-US', new_email)

        self._register_user(register_url, new_username, new_email)


        # Ensure the user was sent a welcome email
        welcome_email = mail.outbox[0]
        expected_subject = u'Take the next step to get involved on MDN!'
        expected_to = [new_email]
        eq_(expected_subject, welcome_email.subject)
        eq_(expected_to, welcome_email.to)
        ok_(u'Hi %s' % new_username in welcome_email.body)


    @mock.patch('devmo.helpers.strings_are_translated')
    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    @mock.patch('kuma.users.views._verify_browserid')
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_new_account_translated_email(self,
                               _verify_browserid,
                               unsubscribe,
                               subscribe,
                               lookup_user,
                               strings_are_translated
                              ):
        new_email = 'never.before.seen@example.com'
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        _verify_browserid.return_value = {'email': new_email}
        strings_are_translated.return_value = True

        Switch.objects.create(name='welcome_email', active=True)
        new_username = 'neverbefore'

        try:
            User.objects.get(email=new_email)
            ok_(False, "User for email should not yet exist")
        except User.DoesNotExist:
            pass

        register_url = self._signin_new_email('fr', new_email)

        self._register_user(register_url, new_username, new_email)


        # Ensure the user was sent a welcome email
        strings_are_translated.assert_called_once_with(WELCOME_EMAIL_STRINGS,
                                                       'fr')
        welcome_email = mail.outbox[0]
        expected_subject = u'Take the next step to get involved on MDN!'
        expected_to = [new_email]
        eq_(expected_subject, welcome_email.subject)
        eq_(expected_to, welcome_email.to)
        ok_(u'Hi %s' % new_username in welcome_email.body)


    @mock.patch('devmo.helpers.strings_are_translated')
    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    @mock.patch('kuma.users.views._verify_browserid')
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_new_account_untranslated_email(self,
                               _verify_browserid,
                               unsubscribe,
                               subscribe,
                               lookup_user,
                               strings_are_translated
                              ):
        new_email = 'never.before.seen@example.com'
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        _verify_browserid.return_value = {'email': new_email}
        strings_are_translated.return_value = False

        Switch.objects.create(name='welcome_email', active=True)
        new_username = 'neverbefore'

        try:
            User.objects.get(email=new_email)
            ok_(False, "User for email should not yet exist")
        except User.DoesNotExist:
            pass

        register_url = self._signin_new_email('de', new_email)

        self._register_user(register_url, new_username, new_email)


        # Ensure the user was sent a welcome email
        strings_are_translated.assert_called_once_with(WELCOME_EMAIL_STRINGS,
                                                       'de')
        eq_([], mail.outbox)


    @mock.patch('kuma.users.views._verify_browserid')
    def test_valid_assertion_with_existing_account_login(self,
                                                         _verify_browserid):
        """ Removed the existing user form: we don't auth the password with
        MindTouch anymore """
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
        eq_(0, form.length)

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    @mock.patch('kuma.users.views._verify_browserid')
    def test_valid_assertion_changing_email(self, _verify_browserid,
                                                        unsubscribe,
                                                        subscribe,
                                                        lookup_user):
        # just need to be authenticated, not necessarily BrowserID
        self.client.login(username='testuser', password='testpass')

        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        _verify_browserid.return_value = {'email': 'testuser+changed@test.com'}

        resp = self.client.post(reverse('users.browserid_change_email',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)
        ok_('profiles/testuser/edit' in resp['Location'])

        resp = self.client.get(reverse('users.profile_edit', locale='en-US',
                                       args=['testuser', ]))
        eq_(200, resp.status_code)
        doc = pq(resp.content)
        ok_('testuser+changed@test.com' in doc.find('li#field_email').text())

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    @mock.patch('kuma.users.views._verify_browserid')
    def test_valid_assertion_doesnt_steal_email(self, _verify_browserid,
                                                        unsubscribe,
                                                        subscribe,
                                                        lookup_user):
        # just need to be authenticated, not necessarily BrowserID
        self.client.login(username='testuser', password='testpass')

        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        _verify_browserid.return_value = {'email': 'testuser2@test.com'}

        # doesn't change email if the new email already belongs to another user
        resp = self.client.post(reverse('users.browserid_change_email',
                                        locale='en-US'),
                                {'assertion': 'PRETENDTHISISVALID'})
        eq_(302, resp.status_code)
        ok_('change_email' in resp['Location'])

        resp = self.client.get(reverse('users.profile_edit', locale='en-US',
                                       args=['testuser', ]))
        eq_(200, resp.status_code)
        doc = pq(resp.content)
        ok_('testuser@test.com' in doc.find('li#field_email').text())


class OldProfileTestCase(TestCase):
    fixtures = ['test_users.json']

    def test_old_profile_url_gone(self):
        resp = self.client.get('/users/edit', follow=True)
        eq_(404, resp.status_code)


class BanTestCase(TestCase):
    fixtures = ['test_users.json']

    @attr('bans')
    def test_ban_permission(self):
        """The ban permission controls access to the ban view."""
        client = LocalizingClient()
        admin = User.objects.get(username='admin')
        testuser = User.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        client.login(username='testuser',
                     password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': admin.id})
        resp = client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(settings.LOGIN_URL in resp['Location'])
        client.logout()

        # admin has ban permission, can ban.
        client.login(username='admin',
                     password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})
        resp = client.get(ban_url)
        eq_(200, resp.status_code)

    @attr('bans')
    def test_ban_view(self):
        testuser = User.objects.get(username='testuser')
        admin = User.objects.get(username='admin')

        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = client.post(ban_url, data)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])

        testuser_banned = User.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        ok_(bans.count())


class ProfileViewsTest(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client = LocalizingClient()
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    def _get_current_form_field_values(self, doc):
        # Scrape out the existing significant form field values.
        form = dict()
        for fn in ('email', 'fullname', 'title', 'organization', 'location',
                   'irc_nickname', 'bio', 'interests', 'country', 'format'):
            form[fn] = doc.find('#profile-edit *[name="%s"]' % fn).val()
        form['country'] = 'us'
        form['format'] = 'html'
        return form

    @attr('docs_activity')
    def test_profile_view(self):
        """A user profile can be viewed"""
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('users.profile', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(profile.user.username,
            doc.find('#profile-head.vcard .nickname').text())
        eq_(profile.fullname,
            doc.find('#profile-head.vcard .fn').text())
        eq_(profile.title,
            doc.find('#profile-head.vcard .title').text())
        eq_(profile.organization,
            doc.find('#profile-head.vcard .org').text())
        eq_(profile.location,
            doc.find('#profile-head.vcard .loc').text())
        eq_('IRC: ' + profile.irc_nickname,
            doc.find('#profile-head.vcard .irc').text())
        eq_(profile.bio,
            doc.find('#profile-head.vcard .bio').text())

    def test_my_profile_view(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get('/profile/')
        eq_(302, resp.status_code)
        ok_(reverse('users.profile', args=(u.username,)) in
            resp['Location'])

    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        (user, profile) = create_profile()

        url = '%s?page=asdf' % reverse('users.profile', args=(user.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            ok_(False, "Non-numeric page number should not cause an error")

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit(self,
                            unsubscribe,
                            subscribe,
                            lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('users.profile', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(0, doc.find('#profile-head .edit .button').length)

        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile', args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        edit_button = doc.find('#profile-head .edit #edit-profile')
        eq_(1, edit_button.length)

        url = edit_button.attr('href')
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(profile.fullname,
            doc.find('#profile-edit input[name="fullname"]').val())
        eq_(profile.title,
            doc.find('#profile-edit input[name="title"]').val())
        eq_(profile.organization,
            doc.find('#profile-edit input[name="organization"]').val())
        eq_(profile.location,
            doc.find('#profile-edit input[name="location"]').val())
        eq_(profile.irc_nickname,
            doc.find('#profile-edit input[name="irc_nickname"]').val())

        new_attrs = dict(
            email='testuser@test.com',
            fullname="Another Name",
            title="Another title",
            organization="Another org",
            country="us",
            format="html"
        )

        r = self.client.post(url, new_attrs, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('#profile-head').length)
        eq_(new_attrs['fullname'],
            doc.find('#profile-head .main .fn').text())
        eq_(new_attrs['title'],
            doc.find('#profile-head .info .title').text())
        eq_(new_attrs['organization'],
            doc.find('#profile-head .info .org').text())

        profile = UserProfile.objects.get(user__username=user.username)
        eq_(new_attrs['fullname'], profile.fullname)
        eq_(new_attrs['title'], profile.title)
        eq_(new_attrs['organization'], profile.organization)

    def test_my_profile_edit(self):
        u = User.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get('/profile/edit')
        eq_(302, resp.status_code)
        ok_(reverse('users.profile_edit', args=(u.username,)) in
            resp['Location'])

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_beta(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_(None, doc.find('input#id_beta').attr('checked'))

        form = self._get_current_form_field_values(doc)
        form['beta'] = True

        r = self.client.post(url, form, follow=True)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        eq_('checked', doc.find('input#id_beta').attr('checked'))

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_websites(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True

        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_sites = {
            u'website': u'http://example.com/',
            u'twitter': u'http://twitter.com/lmorchard',
            u'github': u'http://github.com/lmorchard',
            u'stackoverflow': u'http://stackoverflow.com/users/lmorchard',
            u'linkedin': u'https://www.linkedin.com/in/testuser',
            u'mozillians': u'https://mozillians.org/u/testuser',
            u'facebook': u'https://www.facebook.com/test.user'
        }

        form = self._get_current_form_field_values(doc)

        # Fill out the form with websites.
        form.update(dict(('websites_%s' % k, v)
                    for k, v in test_sites.items()))

        # Submit the form, verify redirect to profile detail
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        # Verify the websites are saved in the profile.
        eq_(test_sites, p.websites)

        # Verify the saved websites appear in the editing form
        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)
        for k, v in test_sites.items():
            eq_(v, doc.find('#profile-edit *[name="websites_%s"]' % k).val())

        # Come up with some bad sites, either invalid URL or bad URL prefix
        bad_sites = {
            u'website': u'HAHAHA WHAT IS A WEBSITE',
            u'twitter': u'http://facebook.com/lmorchard',
            u'stackoverflow': u'http://overqueueblah.com/users/lmorchard',
        }
        form.update(dict(('websites_%s' % k, v)
                    for k, v in bad_sites.items()))

        # Submit the form, verify errors for all of the bad sites
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-edit').length)
        tmpl = '#profile-edit #elsewhere .%s .errorlist'
        for n in ('website', 'twitter', 'stackoverflow'):
            eq_(1, doc.find(tmpl % n).length)

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_interests(self,
                                    unsubscribe,
                                    subscribe,
                                    lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True

        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = self._get_current_form_field_values(doc)

        form['interests'] = ', '.join(test_tags)

        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)
        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        result_tags = [t.name.replace('profile:interest:', '')
                for t in p.tags.all_ns('profile:interest:')]
        result_tags.sort()
        test_tags.sort()
        eq_(test_tags, result_tags)

        test_expertise = ['css', 'canvas']
        form['expertise'] = ', '.join(test_expertise)
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('#profile-head').length)

        p = UserProfile.objects.get(user=user)

        result_tags = [t.name.replace('profile:expertise:', '')
                for t in p.tags.all_ns('profile:expertise')]
        result_tags.sort()
        test_expertise.sort()
        eq_(test_expertise, result_tags)

        # Now, try some expertise tags not covered in interests
        test_expertise = ['css', 'canvas', 'mobile', 'movies']
        form['expertise'] = ', '.join(test_expertise)
        r = self.client.post(url, form, follow=True)
        doc = pq(r.content)

        eq_(1, doc.find('.error #id_expertise').length)

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_bug_709938_interests(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
                password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(user.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        test_tags = [u'science,Technology,paradox,knowledge,modeling,big data,'
                     u'vector,meme,heuristics,harmony,mathesis universalis,'
                     u'symmetry,mathematics,computer graphics,field,chemistry,'
                     u'religion,astronomy,physics,biology,literature,'
                     u'spirituality,Art,Philosophy,Psychology,Business,Music,'
                     u'Computer Science']

        form = self._get_current_form_field_values(doc)

        form['interests'] = test_tags

        r = self.client.post(url, form, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, doc.find('ul.errorlist li').length)
        assert ('Ensure this value has at most 255 characters'
                in doc.find('ul.errorlist li').text())

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_bug_698126_l10n(self, unsubscribe, subscribe, lookup_user):
        """Test that the form field names are localized"""
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        user = User.objects.get(username='testuser')
        self.client.login(username=user.username,
            password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
            args=(user.username,))
        r = self.client.get(url, follow=True)
        for field in r.context['form'].fields:
            # if label is localized it's a lazy proxy object
            ok_(not isinstance(
                r.context['form'].fields[field].label, basestring),
                'Field %s is a string!' % field)

    def _break(self, url, r):
        logging.debug("URL  %s" % url)
        logging.debug("STAT %s" % r.status_code)
        logging.debug("HEAD %s" % r.items())
        logging.debug("CONT %s" % r.content)
        ok_(False)

    def test_bug_811751_banned_profile(self):
        """A banned user's profile should not be viewable"""
        profile = UserProfile.objects.get(user__username='testuser')
        user = profile.user
        url = reverse('users.profile', args=(user.username,))

        # Profile viewable if not banned
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

        # Ban User
        admin = User.objects.get(username='admin')
        testuser = User.objects.get(username='testuser')
        ban = UserBan(user=testuser, by=admin,
                      reason='Banned by unit test.',
                      is_active=True)
        ban.save()

        # Profile not viewable if banned
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # Admin can view banned user's profile
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)
