import mock
import json
from urlparse import urlparse, parse_qs

from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.sites.models import Site
from django.core.paginator import PageNotAnInteger

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.providers import registry
from allauth.tests import MockedResponse, mocked_response

from kuma.core.tests import mock_lookup_user
from kuma.core.urlresolvers import reverse

from . import UserTestCase, user, email
from ..models import UserProfile, UserBan
from ..signup import SignupForm
from ..providers.github.provider import KumaGitHubProvider

TESTUSER_PASSWORD = 'testpass'


class OldProfileTestCase(UserTestCase):
    localizing_client = True

    def test_old_profile_url_gone(self):
        response = self.client.get('/users/edit', follow=True)
        eq_(404, response.status_code)


class BanTestCase(UserTestCase):
    localizing_client = True

    @attr('bans')
    def test_ban_permission(self):
        """The ban permission controls access to the ban view."""
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username='testuser',
                          password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': admin.id})
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(str(settings.LOGIN_URL) in resp['Location'])
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})
        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

    @attr('bans')
    def test_ban_view(self):
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = self.client.post(ban_url, data)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])

        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        ok_(bans.count())

    @attr('bans')
    def test_bug_811751_banned_profile(self):
        """A banned user's profile should not be viewable"""
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.profile', args=(testuser.username,))

        # Profile viewable if not banned
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

        # Ban User
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)

        # Profile not viewable if banned
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # Admin can view banned user's profile
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)


class ProfileViewsTest(UserTestCase):
    localizing_client = True

    def setUp(self):
        super(ProfileViewsTest, self).setUp()
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    def _get_current_form_field_values(self, doc):
        # Scrape out the existing significant form field values.
        form = dict()
        for fn in ('username', 'email', 'fullname', 'title', 'organization',
                   'location', 'irc_nickname', 'bio', 'interests'):
            form[fn] = doc.find('#profile-edit *[name="profile-%s"]' %
                                fn).val()
        form['country'] = 'us'
        form['format'] = 'html'
        return form

    @attr('docs_activity')
    def test_profile_view(self):
        """A user profile can be viewed"""
        profile = UserProfile.objects.get(user__username='testuser')
        url = reverse('users.profile', args=(profile.user.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

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
            doc.find('#profile-head.vcard .profile-bio').text())

    def test_my_profile_view(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_profile'))
        eq_(302, resp.status_code)
        ok_(reverse('users.profile', args=(u.username,)) in
            resp['Location'])

    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        testuser = self.user_model.objects.get(username='testuser')

        url = '%s?page=asdf' % reverse('users.profile',
                                       args=(testuser.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            self.fail("Non-numeric page number should not cause an error")

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        profile = UserProfile.objects.get(user__username='testuser')
        url = reverse('users.profile', args=(profile.user.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(0, doc.find('#profile-head .edit .button').length)

        self.client.login(username=profile.user.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile', args=(profile.user.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        edit_button = doc.find('#profile-head .profile-buttons #edit-profile')
        eq_(1, edit_button.length)

        url = edit_button.attr('href')
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        eq_(profile.fullname,
            doc.find('#profile-edit input[name="profile-fullname"]').val())
        eq_(profile.title,
            doc.find('#profile-edit input[name="profile-title"]').val())
        eq_(profile.organization,
            doc.find('#profile-edit input[name="profile-organization"]').val())
        eq_(profile.location,
            doc.find('#profile-edit input[name="profile-location"]').val())
        eq_(profile.irc_nickname,
            doc.find('#profile-edit input[name="profile-irc_nickname"]').val())

        new_attrs = {
            'profile-email': 'testuser@test.com',
            'profile-fullname': "Another Name",
            'profile-title': "Another title",
            'profile-organization': "Another org",
            'profile-country': "us",
            'profile-format': "html"
        }

        response = self.client.post(url, new_attrs, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('#profile-head').length)
        eq_(new_attrs['profile-fullname'],
            doc.find('#profile-head .fn').text())
        eq_(new_attrs['profile-title'],
            doc.find('#profile-head .profile-info .title').text())
        eq_(new_attrs['profile-organization'],
            doc.find('#profile-head .profile-info .org').text())

        profile = UserProfile.objects.get(user__username=profile.user.username)
        eq_(new_attrs['profile-fullname'], profile.fullname)
        eq_(new_attrs['profile-title'], profile.title)
        eq_(new_attrs['profile-organization'], profile.organization)

    def test_my_profile_edit(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_profile_edit'))
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
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(None, doc.find('input#id_profile-beta').attr('checked'))

        form = self._get_current_form_field_values(doc)
        form['profile-beta'] = True

        self.client.post(url, form, follow=True)

        url = reverse('users.profile_edit',
                      args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_('checked', doc.find('input#id_profile-beta').attr('checked'))

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_profile_edit_websites(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True

        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

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
        form.update(dict(('profile-websites_%s' % k, v)
                    for k, v in test_sites.items()))

        # Submit the form, verify redirect to profile detail
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#profile-head').length)

        profile = UserProfile.objects.get(user=testuser)

        # Verify the websites are saved in the profile.
        eq_(test_sites, profile.websites)

        # Verify the saved websites appear in the editing form
        url = reverse('users.profile_edit',
                      args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        for k, v in test_sites.items():
            eq_(v,
                doc.find('#profile-edit *[name="profile-websites_%s"]' %
                         k).val())

        # Come up with some bad sites, either invalid URL or bad URL prefix
        bad_sites = {
            u'website': u'HAHAHA WHAT IS A WEBSITE',
            u'twitter': u'http://facebook.com/lmorchard',
            u'stackoverflow': u'http://overqueueblah.com/users/lmorchard',
        }
        form.update(dict(('profile-websites_%s' % k, v)
                    for k, v in bad_sites.items()))

        # Submit the form, verify errors for all of the bad sites
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#profile-edit').length)
        tmpl = '#profile-edit #profiles .%s .errorlist'
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

        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = self._get_current_form_field_values(doc)

        form['profile-interests'] = ', '.join(test_tags)

        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#profile-head').length)

        profile = UserProfile.objects.get(user=testuser)

        result_tags = [t.name.replace('profile:interest:', '')
                       for t in profile.tags.all_ns('profile:interest:')]
        result_tags.sort()
        test_tags.sort()
        eq_(test_tags, result_tags)

        test_expertise = ['css', 'canvas']
        form['profile-expertise'] = ', '.join(test_expertise)
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('#profile-head').length)

        profile = UserProfile.objects.get(user=testuser)

        result_tags = [t.name.replace('profile:expertise:', '')
                       for t in profile.tags.all_ns('profile:expertise')]
        result_tags.sort()
        test_expertise.sort()
        eq_(test_expertise, result_tags)

        # Now, try some expertise tags not covered in interests
        test_expertise = ['css', 'canvas', 'mobile', 'movies']
        form['profile-expertise'] = ', '.join(test_expertise)
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('.error #id_profile-expertise').length)

    @mock.patch('basket.lookup_user')
    @mock.patch('basket.subscribe')
    @mock.patch('basket.unsubscribe')
    def test_bug_709938_interests(self, unsubscribe, subscribe, lookup_user):
        lookup_user.return_value = mock_lookup_user()
        subscribe.return_value = True
        unsubscribe.return_value = True
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_tags = [u'science,Technology,paradox,knowledge,modeling,big data,'
                     u'vector,meme,heuristics,harmony,mathesis universalis,'
                     u'symmetry,mathematics,computer graphics,field,chemistry,'
                     u'religion,astronomy,physics,biology,literature,'
                     u'spirituality,Art,Philosophy,Psychology,Business,Music,'
                     u'Computer Science']

        form = self._get_current_form_field_values(doc)

        form['profile-interests'] = test_tags

        response = self.client.post(url, form, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
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
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit',
                      args=(testuser.username,))
        response = self.client.get(url, follow=True)
        for field in response.context['profile_form'].fields:
            # if label is localized it's a lazy proxy object
            ok_(not isinstance(
                response.context['profile_form'].fields[field].label, basestring),
                'Field %s is a string!' % field)

    def test_bug_1174804(self):
        """Test that the newsletter form field are safely rendered"""
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.profile_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(len(doc.find('input[name=newsletter-format]')), 2)


class Test404Case(UserTestCase):

    def test_404_logins(self):
        """The login buttons should display on the 404 page"""
        response = self.client.get('/something-doesnt-exist', follow=True)
        doc = pq(response.content)

        login_block = doc.find('.socialaccount-providers')
        ok_(len(login_block) > 0)
        eq_(404, response.status_code)

    def test_404_already_logged_in(self):
        """
        The login buttons should not display on the 404 page when the
        user is logged in
        """
        # View page as a logged in user
        self.client.login(username='testuser',
                          password='testpass')
        response = self.client.get('/something-doesnt-exist', follow=True)
        doc = pq(response.content)

        login_block = doc.find('.socialaccount-providers')
        eq_(len(login_block), 0)
        eq_(404, response.status_code)
        self.client.logout()


class AllauthPersonaTestCase(UserTestCase):
    """
    Test sign-up/in flow with Persona.
    """
    existing_persona_email = 'testuser@test.com'
    existing_persona_username = 'testuser'
    localizing_client = False

    def test_persona_auth_failure(self):
        """
        Failed Persona auth does not crash or otherwise error, but
        correctly redirects to an explanatory page.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'failure',
                'reason': 'this email address has been naughty'
            }
            response = self.client.post(reverse('persona_login'),
                                        follow=True)
            eq_(200, response.status_code)
            eq_(response.redirect_chain,
                [('http://testserver/users/persona/complete?process=&next=',
                  302)])

    def test_persona_auth_success(self):
        """
        Successful Persona auth of a new (i.e., no connected social
        account with that email) user redirects to the signup
        completion page.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': 'views_persona_auth@example.com',
            }
            response = self.client.post(reverse('persona_login'),
                                        follow=True)
            eq_(response.status_code, 200)
            expected_redirects = [
                ('http://testserver/users/persona/complete?process=&next=',
                 302),
                ('http://testserver/users/account/signup',
                 302),
            ]
            for red in expected_redirects:
                ok_(red in response.redirect_chain)

    def test_persona_signin(self):
        """
        When an existing user signs in with Persona, using the email
        address associated with their account, authentication is
        successful and redirects to the home page when no explicit
        'next' is provided.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': self.existing_persona_email,
            }
            response = self.client.post(reverse('persona_login'),
                                        follow=True)
            eq_(response.status_code, 200)
            expected_redirects = [
                ('http://testserver/users/persona/complete?process=&next=',
                 302),
                ('http://testserver/en-US/',
                 301)
            ]
            for red in expected_redirects:
                ok_(red in response.redirect_chain)

    def test_persona_signin_next(self):
        """
        When an existing user successfully authenticates with Persona,
        from a page which supplied a 'next' parameter, they are
        redirected back to that page following authentication.
        """
        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': self.existing_persona_email,
            }
            doc_url = reverse('wiki.document', args=['article-title'],
                              locale=settings.WIKI_DEFAULT_LANGUAGE)
            response = self.client.post(reverse('persona_login'),
                                        data={'next': doc_url},
                                        follow=True)
            ok_(('http://testserver%s' % doc_url, 302) in response.redirect_chain)

    def test_persona_signup_create_django_user(self):
        """
        Signing up with Persona creates a new Django User instance.
        """
        persona_signup_email = 'views_persona_django_user@example.com'
        persona_signup_username = 'views_persona_django_user'

        with mock.patch('requests.post') as requests_mock:
            old_count = self.user_model.objects.count()
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': persona_signup_email,
            }
            self.client.post(reverse('persona_login'), follow=True)
            data = {'website': '',
                    'username': persona_signup_username,
                    'email': persona_signup_email,
                    'newsletter': True,
                    'terms': True}
            signup_url = reverse('socialaccount_signup',
                                 locale=settings.WIKI_DEFAULT_LANGUAGE)
            response = self.client.post(signup_url, data=data, follow=True)
            eq_(response.status_code, 200)
            eq_(response.context['form'].errors,
                {'__all__': ['You must agree to the privacy policy.']})

            # We didn't create a new user.
            eq_(old_count, self.user_model.objects.count())

            data.update({'agree': True})
            response = self.client.post(signup_url, data=data, follow=True)
            eq_(response.status_code, 200)
            # not on the signup page anymore
            ok_('form' not in response.context)

            # Did we get a new user?
            eq_(old_count + 1, self.user_model.objects.count())

            # Does it have the right attributes?
            testuser = None
            try:
                testuser = self.user_model.objects.order_by('-date_joined')[0]
            except IndexError:
                pass
            ok_(testuser)
            ok_(testuser.is_active)
            eq_(persona_signup_username, testuser.username)
            eq_(persona_signup_email, testuser.email)
            ok_(testuser.password.startswith(UNUSABLE_PASSWORD_PREFIX))

    def test_persona_signup_create_socialaccount(self):
        """
        Signing up with Persona creates a new SocialAccount instance.
        """
        persona_signup_email = 'views_persona_socialaccount@example.com'
        persona_signup_username = 'views_persona_socialaccount'

        with mock.patch('requests.post') as requests_mock:
            requests_mock.return_value.json.return_value = {
                'status': 'okay',
                'email': persona_signup_email,
            }
            self.client.post(reverse('persona_login'), follow=True)
            data = {'website': '',
                    'username': persona_signup_username,
                    'email': persona_signup_email,
                    'terms': True}
            signup_url = reverse('socialaccount_signup',
                                 locale=settings.WIKI_DEFAULT_LANGUAGE)
            self.client.post(signup_url, data=data, follow=True)
            try:
                socialaccount = (SocialAccount.objects
                                              .filter(user__username=persona_signup_username))[0]
            except IndexError:
                socialaccount = None
            ok_(socialaccount is not None)
            eq_('persona', socialaccount.provider)
            eq_(persona_signup_email, socialaccount.uid)
            eq_({'status': 'okay', 'email': persona_signup_email},
                socialaccount.extra_data)
            testuser = self.user_model.objects.get(username=persona_signup_username)
            eq_(testuser.id, socialaccount.user.id)


class KumaGitHubTests(UserTestCase):
    localizing_client = False
    mocked_user_response = """
        {
            "login": "%(username)s",
            "id": 1,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "gravatar_id": "somehexcode",
            "url": "https://api.github.com/users/octocat",
            "html_url": "https://github.com/octocat",
            "followers_url": "https://api.github.com/users/octocat/followers",
            "following_url": "https://api.github.com/users/octocat/following{/other_user}",
            "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
            "organizations_url": "https://api.github.com/users/octocat/orgs",
            "repos_url": "https://api.github.com/users/octocat/repos",
            "events_url": "https://api.github.com/users/octocat/events{/privacy}",
            "received_events_url": "https://api.github.com/users/octocat/received_events",
            "type": "User",
            "site_admin": false,
            "name": "monalisa octocat",
            "company": "GitHub",
            "blog": "https://github.com/blog",
            "location": "San Francisco",
            "email": %(public_email)s,
            "hireable": false,
            "bio": "There once was...",
            "public_repos": 2,
            "public_gists": 1,
            "followers": 20,
            "following": 0,
            "created_at": "2008-01-14T04:33:35Z",
            "updated_at": "2008-01-14T04:33:35Z"
        }"""
    mocked_email_response = """
        [
            {
                "email": "%(verified_email)s",
                "verified": true,
                "primary": true
            }
        ]"""

    def get_login_response_json(self, with_refresh_token=True):
        rt = ''
        if with_refresh_token:
            rt = ',"refresh_token": "testrf"'
        return """{
            "uid":"weibo",
            "access_token":"testac"
            %s }""" % rt

    def setUp(self):
        self.signup_url = reverse('socialaccount_signup',
                                  locale=settings.WIKI_DEFAULT_LANGUAGE)
        self.provider = registry.by_id(KumaGitHubProvider.id)
        app = SocialApp.objects.create(provider=self.provider.id,
                                       name=self.provider.id,
                                       client_id='app123id',
                                       key=self.provider.id,
                                       secret='dummy')
        app.sites.add(Site.objects.get_current())

    def test_login(self):
        resp = self.login()
        self.assertRedirects(resp, self.signup_url)

    def test_matching_user(self):
        self.login()
        response = self.client.get(self.signup_url)
        self.assertTrue('matching_user' in response.context)
        self.assertEqual(response.context['matching_user'], None)
        octocat = user(username='octocat', save=True)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context['matching_user'], octocat)

    def test_email_addresses(self):
        self.login(username='octocat2')
        response = self.client.get(self.signup_url)
        email_address = response.context['email_addresses']

        # first check if the public email address has been found
        self.assertTrue('octocat@github.com' in email_address)
        self.assertEqual(email_address['octocat@github.com'],
                         {'verified': False,
                          'email': 'octocat@github.com',
                          'primary': False})
        # then check if the private and verified-at-GitHub email address
        # has been found
        self.assertTrue('octo.cat@github-inc.com' in email_address)
        self.assertEqual(email_address['octo.cat@github-inc.com'],
                         {'verified': True,
                          'email': 'octo.cat@github-inc.com',
                          'primary': True})
        # then check if the radio button's default value is the public email address
        self.assertEqual(response.context["form"].initial["email"], 'octocat@github.com')

        unverified_email = 'o.ctocat@gmail.com'
        data = {
            'website': '',
            'username': 'octocat',
            'email': SignupForm.other_email_value,  # = use other_email
            'other_email': unverified_email,
            'terms': True
        }
        self.assertFalse((EmailAddress.objects.filter(email=unverified_email)
                                              .exists()))
        response = self.client.post(self.signup_url, data=data, follow=True)
        unverified_email_addresses = EmailAddress.objects.filter(email=unverified_email)
        self.assertTrue(unverified_email_addresses.exists())
        self.assertEquals(unverified_email_addresses.count(), 1)
        self.assertTrue(unverified_email_addresses[0].primary)
        self.assertFalse(unverified_email_addresses[0].verified)

    def test_email_addresses_with_no_public(self):
        self.login(username='private_octocat',
                   verified_email='octocat@github.com',
                   public_email=None)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context["form"].initial["email"], 'octocat@github.com')

    def test_matching_accounts(self):
        testemail = 'octo.cat.III@github-inc.com'
        self.login(username='octocat3', verified_email=testemail)
        response = self.client.get(self.signup_url)
        self.assertEqual(list(response.context['matching_accounts']),
                         [])
        # assuming there is already a Persona account with the given email
        # address
        octocat3 = user(username='octocat3', is_active=True,
                        email=testemail, password='test', save=True)
        social_account = SocialAccount.objects.create(uid=testemail,
                                                      provider='persona',
                                                      user=octocat3)
        response = self.client.get(self.signup_url)
        self.assertTrue(response.context['matching_accounts'],
                        [social_account])

    def test_account_tokens(self, multiple_login=False):
        testemail = 'account_token@acme.com'
        testuser = user(username='user', is_active=True,
                        email=testemail, password='test', save=True)
        email(user=testuser, email=testemail,
              primary=True, verified=True, save=True)
        self.client.login(username=testuser.username,
                          password='test')
        self.login(process='connect')
        if multiple_login:
            self.login(with_refresh_token=False, process='connect')
        # get account
        social_account = SocialAccount.objects.get(user=testuser,
                                                   provider=self.provider.id)
        # get token
        social_token = social_account.socialtoken_set.get()
        # verify access_token and refresh_token
        self.assertEqual('testac', social_token.token)
        self.assertEqual(social_token.token_secret,
                         json.loads(self.get_login_response_json(
                             with_refresh_token=True)).get(
                                 'refresh_token', ''))

    def test_account_refresh_token_saved_next_login(self):
        """
        fails if a login missing a refresh token, deletes the previously
        saved refresh token. Systems such as google's oauth only send
        a refresh token on first login.
        """
        self.test_account_tokens(multiple_login=True)

    def login(self,
              username='octocat',
              verified_email='octo.cat@github-inc.com',
              process='login', with_refresh_token=True,
              public_email='octocat@github.com'):
        resp = self.client.get(reverse('github_login',
                                       locale=settings.WIKI_DEFAULT_LANGUAGE),
                               {'process': process})
        path = urlparse(resp['location'])
        query = parse_qs(path.query)
        complete_url = reverse('github_callback', unprefixed=True)
        self.assertGreater(query['redirect_uri'][0]
                           .find(complete_url), 0)
        response_json = self.get_login_response_json(
            with_refresh_token=with_refresh_token)
        with mocked_response(
            MockedResponse(200, response_json,
                           {'content-type': 'application/json'}),
                MockedResponse(200,
                               self.mocked_user_response %
                               {'username': username,
                                'public_email': json.dumps(public_email)}),
                MockedResponse(200,
                               self.mocked_email_response %
                               {'verified_email': verified_email})):
            resp = self.client.get(complete_url,
                                   {'code': 'test',
                                    'state': query['state'][0]},
                                   follow=True)
        return resp
