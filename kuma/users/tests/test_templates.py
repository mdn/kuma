import json
import pytest
import requests_mock
from constance import config as constance_config
from constance.test.utils import override_config
from django.conf import settings
from mock import patch
from pyquery import PyQuery as pq
from waffle.models import Flag

from kuma.core.tests import eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.wiki.tests import document as create_document, revision as create_revision

from . import SampleRevisionsMixin, UserTestCase
from .test_views import TESTUSER_PASSWORD
from ..models import UserBan


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


@pytest.mark.bans
class BanTestCase(UserTestCase):

    def test_common_reasons_in_template(self):
        # The common reasons to ban users (from constance) should be in template
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        reasons_to_ban_found = page.find('.ban-common-reason')
        reasons_to_ban_expected = json.loads(
            constance_config.COMMON_REASONS_TO_BAN_USERS
        )

        eq_(len(reasons_to_ban_found), len(reasons_to_ban_expected))
        for reason in reasons_to_ban_found:
            ok_(reason.text in reasons_to_ban_expected)

    @override_config(COMMON_REASONS_TO_BAN_USERS='Not valid JSON')
    def test_common_reasons_error(self):
        # If there is an error in getting the common reasons from constance,
        # then 'Spam' should still show up in the template as the default
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        reasons_to_ban_found = page.find('.ban-common-reason')
        reasons_to_ban_expected = ['Spam']

        eq_(len(reasons_to_ban_found), len(reasons_to_ban_expected))
        for reason in reasons_to_ban_found:
            ok_(reason.text in reasons_to_ban_expected)

    @override_config(COMMON_REASONS_TO_BAN_USERS='[]')
    def test_common_reasons_empty(self):
        # If the list of common reasons to ban users in constance is empty,
        # then 'Spam' should still show up in the template as the default
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'user_id': testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        reasons_to_ban_found = page.find('.ban-common-reason')
        reasons_to_ban_expected = ['Spam']

        eq_(len(reasons_to_ban_found), len(reasons_to_ban_expected))
        for reason in reasons_to_ban_found:
            ok_(reason.text in reasons_to_ban_expected)


@pytest.mark.bans
class BanAndCleanupTestCase(SampleRevisionsMixin, UserTestCase):
    def test_user_revisions_in_one_click_page_template(self):
        """The user's revisions show up in the ban and cleanup template."""
        # Create 3 revisions for testuser, titled 'Revision 1', 'Revision 2'...
        revisions_expected = self.create_revisions(
            num=3,
            creator=self.testuser,
            document=self.document)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        revisions_found_text = ''
        for rev in revisions_found:
            revisions_found_text += rev.text_content()

        eq_(len(revisions_found), len(revisions_expected))
        # The title for each of the created revisions shows up in the template
        for revision in revisions_expected:
            ok_(revision.title in revisions_found_text)
        # The original revision created by the admin user is not in the template
        ok_(self.original_revision.title not in revisions_found_text)

    def test_no_user_revisions_in_one_click_page_template(self):
        """If the user has no revisions, it should be stated in the template."""
        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        no_revisions = page.find('#ban-and-cleanup-form')

        eq_(len(revisions_found), 0)
        ok_("This user has not created any revisions in the past three days." in no_revisions.text())

    def test_not_banned_user_one_click_page_template_ban_button(self):
        """Test the ban button text for a user that has not been banned."""
        # There are some revisions made by self.testuser; none by self.testuser2
        num_revisions = 3
        self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')

        # For self.testuser (not banned, and revisions need to be reverted) the
        # button on the form should read "Ban User for Spam & Submit Spam"
        # and there should be a link to ban a user for other reasons
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), num_revisions)
        eq_(ban_button.text(), "Ban User for Spam & Submit Spam")
        eq_(len(ban_other_reasons), 1)

        # For self.testuser2 (not banned, no revisions needing to be reverted)
        # the button on the form should read "Ban User for Spam". There should
        # be no link to ban for other reasons
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser2.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), 0)
        eq_(ban_button.text(), "Ban User for Spam")
        eq_(len(ban_other_reasons), 0)

    def test_banned_user_one_click_page_template_ban_button(self):
        """Test the template for a user that has already been banned."""
        # There are some revisions made by self.testuser; none by self.testuser2
        num_revisions = 3
        self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser)

        # Ban both self.testuser and self.testuser2
        UserBan.objects.create(user=self.testuser, by=self.admin,
                               reason='Banned by unit test.',
                               is_active=True)
        UserBan.objects.create(user=self.testuser2, by=self.admin,
                               reason='Banned by unit test.',
                               is_active=True)

        self.client.login(username='admin', password='testpass')

        # For self.testuser (banned, but revisions need to be reverted) the
        # button on the form should read "Submit Spam". There should
        # be no link to ban for other reasons
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')

        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), num_revisions)
        eq_(ban_button.text(), "Submit Spam")
        eq_(len(ban_other_reasons), 0)

        # For self.testuser2 (banned, has no revisions needing to be reverted)
        # there should be no button on the form and no link to
        # ban for other reasons
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser2.id})

        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), 0)
        eq_(len(ban_button), 0)
        eq_(len(ban_other_reasons), 0)


@pytest.mark.bans
class BanUserAndCleanupSummaryTestCase(SampleRevisionsMixin, UserTestCase):

    def test_user_revisions_in_summary_page_template(self):
        """The user's revisions show up in ban and cleanup summary template."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        revisions_expected = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_expected]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_reverted = page.find('#revisions-reverted li')
        revisions_reverted_text = ''
        for rev in revisions_reverted:
            revisions_reverted_text += rev.text_content()

        # Only one of the three revisions (on the same doc) needs to be reverted
        eq_(len(revisions_reverted), 1)
        # The title for the original revision is not in the template
        ok_(self.original_revision.title not in revisions_reverted_text)

    def test_no_user_revisions_summary_page_template(self):
        """If user has no revisions, it should be stated in summary template."""
        # The expected text
        exp_reverted = "The user did not have any revisions that were reverted."
        exp_followup = "The user did not have any revisions needing follow-up."

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        resp = self.client.post(full_ban_url)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_reverted = page.find('#revisions-reverted li')
        revisions_followup = page.find('#revisions-followup li')
        revisions_reverted_section = page.find('#revisions-reverted')
        revisions_followup_section = page.find('#revisions-followup')

        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_followup), 0)
        ok_(exp_reverted in revisions_reverted_section.text())
        ok_(exp_followup in revisions_followup_section.text())

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_user_revisions_submitted_to_akismet_in_template(self, mock_form):
        """If revision submitted to Akismet, summary template states this"""
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # Don't specify document so a new one is created for each revision
        revisions_created = self.create_revisions(
            num=3,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reported_as_spam_text = ''
        for rev in revisions_reported_as_spam:
            revisions_reported_as_spam_text += rev.text_content()

        eq_(len(revisions_reported_as_spam), len(revisions_created))
        # The title for each of the created revisions shows up in the template
        for revision in revisions_created:
            ok_(revision.title in revisions_reported_as_spam_text)
        # The title for the original revision is not in the template
        ok_(self.original_revision.title not in revisions_reported_as_spam_text)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_user_revisions_not_submitted_to_akismet(self, mock_form):
        """If revision not submitted to Akismet, summary template states this"""
        expect_txt = 'The following revisions could not be submitted to Akismet'
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = False

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # Don't specify document so a new one is created for each revision
        revisions_created = self.create_revisions(
            num=3,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_needing_follow_up_section = page.find('#revisions-followup')
        not_submitted = page.find('#not-submitted-to-akismet li')

        # Template should state that the revisions were not submitted to Akismet
        ok_(expect_txt in revisions_needing_follow_up_section.text())
        # All of the revisions should be in the 'not submitted' section
        eq_(len(not_submitted), len(revisions_created))

    def test_delete_link_appears_summary_page(self):
        """
        Delete link should only appear on summary page sometimes.

        This should occur if:
        1.) The user created the document and
        2.) the document has no other revision.
        """
        # Create an original revision on a document by the self.testuser
        new_document = create_document(save=True)
        new_revision = create_revision(
            title='Revision 0',
            document=new_document,
            creator=self.testuser,
            save=True)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [new_revision.id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': new_document.slug},
            force_locale=True)
        delete_link = page.find('#revisions-followup a[href="{url}"]'.format(
            url=delete_url))

        # There should be 1 delete link found
        eq_(len(delete_link), 1)

    def test_delete_link_does_not_appear_summary_page(self):
        """
        Delete link should not only appear on summary page sometimes.

        This should occur if:
        1.) The user did not create the document or
        2.) the document has other revisions.
        """
        # 1.) User makes a revision on another user's document
        testuser_revisions = self.create_revisions(
            num=1,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [testuser_revisions[0].id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': self.document.slug},
            force_locale=True)
        delete_link = page.find('#revisions-followup a[href="{url}"]'.format(
            url=delete_url))

        # There should not be a link to delete the document
        eq_(len(delete_link), 0)

        # User creates a document, but another user makes a revision on it
        new_document = create_document(save=True)
        testuser_revisions = self.create_revisions(
            num=1,
            document=new_document,
            creator=self.testuser)
        create_revision(
            title='Revision 1',
            document=new_document,
            creator=self.testuser2,
            save=True)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [testuser_revisions[0].id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': new_document.slug},
            force_locale=True)
        delete_link = page.find('#revisions-followup a[href="{url}"]'.format(
            url=delete_url))

        # There should not be a link to delete the document
        eq_(len(delete_link), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_list_revisions_reported_as_spam_once_for_distinct_documents(self, mock_form):
        """
        Only 1 revision per document should be shown on the summary page.

        This test verifies that only 1 revision per document shows up in the
        "The following revisions were reported as spam" section
        """
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # There are all on self.document
        revisions_created = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # Since all of the revisions were made on the same document, only 1 of
        # them should be shown in the template
        eq_(len(revisions_reported_as_spam), 1)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_list_revisions_needing_followup_once_for_distinct_documents(self, mock_form):
        """
        Only 1 revision per document should be shown on the summary page.

        This test verifies that only 1 revision per document shows up in the
        "Pages needing follow up" section
        """
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = False

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # There are all on self.document
        revisions_created = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_needing_follow_up = page.find('#manual-revert-needed li')

        # Since all of the revisions were made on the same document, only 1 of
        # them should be shown in the template
        eq_(len(revisions_needing_follow_up), 1)

#    TODO: Phase III:
#    def test_unreverted_changes_in_summary_page_template(self):
#    def test_list_reverted_revisions_once_for_distinct_documents(self):
#        """
#        Only 1 revision per document should be shown on the summary page.
#
#        This test verifies that only 1 revision per document shows up in the
#        "The following revisions were reverted" section
#        """


class ProfileDetailTestCase(UserTestCase):
    def test_user_profile_detail_ban_link(self):
        """
        Tests the user profile page for a user who has been banned.

        The correct text (depending on if the user has been banned or not)
        should be displayed on the ban links.
        """
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        profile_url = reverse('users.user_detail',
                              kwargs={'username': testuser.username})

        # The user is not banned, display appropriate links
        resp = self.client.get(profile_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        ban_link = page.find('#ban_link')
        ban_cleanup_link = page.find('#cleanup_link')
        eq_("Ban User", ban_link.text())
        eq_("Ban User & Clean Up", ban_cleanup_link.text())

        # The user is banned, display appropriate links
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)
        resp = self.client.get(profile_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        ban_link = page.find('#ban_link')
        ban_cleanup_link = page.find('#cleanup_link')
        eq_("Banned", ban_link.text())
        eq_("Clean Up Revisions", ban_cleanup_link.text())
