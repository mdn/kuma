import requests_mock
from django.conf import settings
from pyquery import PyQuery as pq
from waffle.models import Flag

from kuma.core.tests import eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams

from . import UserTestCase
from .test_views import TESTUSER_PASSWORD


def add_persona_verify_response(mock_requests, data):
    mock_requests.post(
        settings.PERSONA_VERIFIER_URL,
        json=data,
        headers={
            'content_type': 'application/json',
        }
    )


@requests_mock.mock()
class SignupTests(UserTestCase):
    localizing_client = False

    def test_signup_page(self, mock_requests):
        add_persona_verify_response(mock_requests, {
            'status': 'okay',
            'email': 'newuser@test.com',
            'audience': 'https://developer-local.allizom.org',
        })

        url = reverse('persona_login')
        response = self.client.post(url, follow=True)

        self.assertNotContains(response, 'Sign In Failure')
        test_strings = ['Create your MDN profile to continue',
                        'choose a username',
                        'having trouble',
                        'I agree',
                        'to Mozilla',
                        'Terms',
                        'Privacy Notice']
        for test_string in test_strings:
            self.assertContains(response, test_string)

    def test_signup_page_disabled(self, mock_requests):
        add_persona_verify_response(mock_requests, {
            'status': 'okay',
            'email': 'newuser@test.com',
            'audience': 'https://developer-local.allizom.org',
        })

        url = reverse('persona_login')

        registration_disabled = Flag.objects.create(
            name='registration_disabled',
            everyone=True
        )
        response = self.client.post(url, follow=True)

        self.assertNotContains(response, 'Sign In Failure')
        self.assertContains(response, 'Profile Creation Disabled')

        # re-enable registration
        registration_disabled.everyone = False
        registration_disabled.save()

        response = self.client.post(url, follow=True)
        test_strings = ['Create your MDN profile to continue',
                        'choose a username',
                        'having trouble']
        for test_string in test_strings:
            self.assertContains(response, test_string)


class AccountEmailTests(UserTestCase):
    localizing_client = True

    def test_account_email_page_requires_signin(self):
        url = reverse('account_email')
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Please sign in')
        ok_(len(response.redirect_chain) > 0)

    def test_account_email_page_single_email(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        url = reverse('account_email')
        response = self.client.get(url)
        self.assertContains(response, 'is your <em>primary</em> email address')
        for test_string in ['Make Primary',
                            'Re-send Confirmation',
                            'Remove']:
            self.assertNotContains(response, test_string)

    def test_account_email_page_multiple_emails(self):
        u = self.user_model.objects.get(username='testuser2')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        url = reverse('account_email')
        response = self.client.get(url)
        for test_string in ['Make Primary',
                            'Re-send Confirmation',
                            'Remove',
                            'Add Email',
                            'Edit profile']:
            self.assertContains(response, test_string)


class SocialAccountConnectionsTests(UserTestCase):
    localizing_client = True

    def test_account_connections_page_requires_signin(self):
        url = reverse('socialaccount_connections')
        response = self.client.get(url, follow=True)
        self.assertContains(response, 'Please sign in')
        ok_(len(response.redirect_chain) > 0)

    def test_account_connections_page(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        url = reverse('socialaccount_connections')
        response = self.client.get(url)

        for test_string in ['Disconnect', 'Connect a new account',
                            'Edit profile', 'Connect with']:
            self.assertContains(response, test_string)


class AllauthPersonaTestCase(UserTestCase):
    existing_persona_email = 'testuser@test.com'
    existing_persona_username = 'testuser'
    localizing_client = False

    @requests_mock.mock()
    def test_persona_auth_failure_copy(self, mock_requests):
        """
        The explanatory page for failed Persona auth contains the
        failure copy, and does not contain success messages or a form
        to choose a username.
        """
        add_persona_verify_response(mock_requests, {
            'status': 'failure',
            'reason': 'this email address has been naughty'
        })
        response = self.client.post(reverse('persona_login'), follow=True)
        for expected_string in ('Account Sign In Failure',
                                'An error occurred while attempting to sign '
                                'in with your account.'):
            self.assertContains(response, expected_string)

        for unexpected_string in (
            'Thanks for signing in to MDN with Persona.',
            ('<form class="submission readable-line-length" method="post" '
             'action="/en-US/users/account/signup">'),
            ('<input name="username" maxlength="30" type="text"'
             ' autofocus="autofocus" required="required" '
             'placeholder="Username" id="id_username" />'),
            '<input type="hidden" name="email" value="',
                '" id="id_email" />'):
            self.assertNotContains(response, unexpected_string)

    @requests_mock.mock()
    def test_persona_auth_success_copy(self, mock_requests):
        """
        Successful Persona auth of a new user displays a success
        message and the Persona-specific signup form, correctly
        populated, and does not display the failure copy.
        """
        persona_signup_email = 'templates_persona_auth_copy@example.com'
        add_persona_verify_response(mock_requests, {
            'status': 'okay',
            'email': persona_signup_email,
        })

        response = self.client.post(reverse('persona_login'),
                                    follow=True)
        for expected_string in (
            # Test that we got:
            #
            # * Persona sign-in success message
            #
            # * Form with action set to the account-signup URL.
            #
            # * Username field, blank
            #
            # * Hidden email address field, pre-populated with the
            #   address used to authenticate to Persona.
            'Thanks for signing in to MDN with Persona.',
            ('<form class="submission readable-line-length" method="post" '
             'action="/en-US/users/account/signup">'),
            ('<input autofocus="autofocus" id="id_username" '
             'maxlength="30" name="username" placeholder="Username" '
             'required="required" type="text" />'),
            ('<input id="id_email" name="email" type="hidden" '
             'value="%s" />' % persona_signup_email)):
            self.assertContains(response, expected_string)

        for unexpected_string in (
            '<Account Sign In Failure',
            '<An error occurred while attempting to sign '
                'in with your account.'):
            self.assertNotContains(response, unexpected_string)

    @requests_mock.mock()
    def test_persona_signin_copy(self, mock_requests):
        """
        After an existing user successfully authenticates with
        Persona, their username, an indication that Persona was used
        to log in, and a logout link appear in the auth tools section
        of the page.
        """
        add_persona_verify_response(mock_requests, {
            'status': 'okay',
            'email': self.existing_persona_email,
        })

        response = self.client.post(reverse('persona_login'), follow=True)
        eq_(response.status_code, 200)

        user_url = reverse(
            'users.user_detail',
            kwargs={
                'username': self.existing_persona_username
            },
            locale=settings.WIKI_DEFAULT_LANGUAGE)
        signout_url = urlparams(
            reverse('account_logout',
                    locale=settings.WIKI_DEFAULT_LANGUAGE),
            next=reverse('home',
                         locale=settings.WIKI_DEFAULT_LANGUAGE))
        parsed = pq(response.content)

        login_info = parsed.find('.oauth-logged-in')
        ok_(len(login_info.children()))

        signed_in_message = login_info.children()[0]
        ok_('title' in signed_in_message.attrib)
        eq_('Signed in with Persona',
            signed_in_message.attrib['title'])

        auth_links = login_info.children()[1].getchildren()
        ok_(len(auth_links))

        user_link = auth_links[0].getchildren()[0]
        ok_('href' in user_link.attrib)
        eq_(user_url, user_link.attrib['href'])

        signout_link = auth_links[1].getchildren()[0]
        ok_('href' in signout_link.attrib)
        eq_(signout_url.replace('%2F', '/'),  # urlparams() encodes slashes
            signout_link.attrib['href'])

    def test_persona_form_present(self):
        """
        When not authenticated, the Persona authentication components,
        with correct data attributes, are present in page contents,
        and the 'next' parameter is filled in.
        """
        all_docs_url = reverse('wiki.all_documents',
                               locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(all_docs_url, follow=True)
        parsed = pq(response.content)
        request_info = '{"siteName": "%(siteName)s", "siteLogo": "%(siteLogo)s"}' % \
                       settings.SOCIALACCOUNT_PROVIDERS['persona']['REQUEST_PARAMETERS']
        stub_attrs = (
            ('data-csrf-token-url', reverse('persona_csrf_token')),
            ('data-request', request_info),
        )
        auth_attrs = (
            ('data-service', 'Persona'),
            ('data-next', all_docs_url),
        )
        stub_persona_form = parsed.find('#_persona_login')
        ok_(len(stub_persona_form) > 0)
        for stub_attr in stub_attrs:
            ok_(stub_persona_form.attr(stub_attr[0]))
            eq_(stub_attr[1], stub_persona_form.attr(stub_attr[0]))
        auth_persona_form = parsed.find('.launch-persona-login')
        ok_(len(auth_persona_form) > 0)
        for auth_attr in auth_attrs:
            ok_(auth_persona_form.attr(auth_attr[0]))
            eq_(auth_attr[1], auth_persona_form.attr(auth_attr[0]))

    @requests_mock.mock()
    def test_persona_signup_copy(self, mock_requests):
        """
        After a new user signs up with Persona, their username, an
        indication that Persona was used to log in, and a logout link
        appear in the auth tools section of the page.
        """
        persona_signup_email = 'templates_persona_signup_copy@example.com'
        persona_signup_username = 'templates_persona_signup_copy'
        add_persona_verify_response(mock_requests, {
            'status': 'okay',
            'email': persona_signup_email,
        })

        self.client.post(reverse('persona_login'), follow=True)
        data = {'website': '',
                'username': persona_signup_username,
                'email': persona_signup_email,
                'terms': True}
        response = self.client.post(
            reverse('socialaccount_signup',
                    locale=settings.WIKI_DEFAULT_LANGUAGE),
            data=data, follow=True)

        user_url = reverse(
            'users.user_detail',
            kwargs={'username': persona_signup_username},
            locale=settings.WIKI_DEFAULT_LANGUAGE)
        signout_url = urlparams(
            reverse('account_logout',
                    locale=settings.WIKI_DEFAULT_LANGUAGE),
            next=reverse('home',
                         locale=settings.WIKI_DEFAULT_LANGUAGE))
        parsed = pq(response.content)

        login_info = parsed.find('.oauth-logged-in')
        ok_(len(login_info.children()))

        signed_in_message = login_info.children()[0]
        ok_('title' in signed_in_message.attrib)
        eq_('Signed in with Persona',
            signed_in_message.attrib['title'])

        auth_links = login_info.children()[1].getchildren()
        ok_(len(auth_links))

        user_link = auth_links[0].getchildren()[0]
        ok_('href' in user_link.attrib)
        eq_(user_url, user_link.attrib['href'])

        signout_link = auth_links[1].getchildren()[0]
        ok_('href' in signout_link.attrib)
        eq_(signout_url.replace('%2F', '/'),  # urlparams() encodes slashes
            signout_link.attrib['href'])
