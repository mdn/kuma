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
from kuma.wiki.models import RevisionAkismetSubmission
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

    def test_not_banned_user_no_revisions_ban_button(self):
        """Test ban button text for a non-banned user who has revisions not submitted as spam."""
        # There are some revisions made by self.testuser
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

    def test_not_banned_user_no_revisions_or_already_spam_ban_button(self):
        """
        Test for a non-banned user with no revisions that can be marked as spam.

        We test the ban button text for a non-banned user who has either
        no revisions or revisions already marked as spam.
        """
        self.client.login(username='admin', password='testpass')
        # For self.testuser (not banned, no revisions needing to be reverted)
        # the button on the form should read "Ban User for Spam". There should
        # be no link to ban for other reasons
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser.id})
        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), 0)
        eq_(ban_button.text(), "Ban User for Spam")
        eq_(len(ban_other_reasons), 0)

        # For self.testuser2 (not banned, revisions already marked as spam)
        # the button on the form should read "Ban User for Spam". There should
        # be no link to ban for other reasons
        # Create some revisions made by self.testuser2 and add a Spam submission for each
        num_revisions = 3
        created_revisions = self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser2)
        for revision in created_revisions:
            revision.akismet_submissions.add(RevisionAkismetSubmission(
                sender=self.testuser2, type="spam")
            )

        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser2.id})
        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), 3)
        eq_(ban_button.text(), "Ban User for Spam")
        eq_(len(ban_other_reasons), 0)

    def test_banned_user_revisions_ban_button(self):
        """Test the template for a banned user with revisions that can be marked as spam."""
        # There are some revisions made by self.testuser; none by self.testuser2
        num_revisions = 3
        self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser)

        # Ban self.testuser
        UserBan.objects.create(user=self.testuser, by=self.admin,
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

    def test_banned_user_no_revisions_or_already_spam_ban_button(self):
        """
        Test for a banned user with no revisions that can be marked as spam.

        We test the ban button text for a banned user who has either
        no revisions or revisions already marked as spam.
        """
        # Ban self.testuser2
        UserBan.objects.create(user=self.testuser2, by=self.admin,
                               reason='Banned by unit test.',
                               is_active=True)
        self.client.login(username='admin', password='testpass')
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

        # For self.testuser2 (banned, revisions already marked as spam)
        # there should be no button on the form and no link to
        # ban for other reasons
        # Create some revisions made by self.testuser2 and add a Spam submission for each
        num_revisions = 3
        created_revisions = self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser2)
        for revision in created_revisions:
            revision.akismet_submissions.add(RevisionAkismetSubmission(
                sender=self.testuser2, type="spam")
            )

        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'user_id': self.testuser2.id})
        resp = self.client.get(ban_url, follow=True)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        eq_(len(revisions_found), 3)
        eq_(len(ban_button), 0)
        eq_(len(ban_other_reasons), 0)


@pytest.mark.bans
class BanUserAndCleanupSummaryTestCase(SampleRevisionsMixin, UserTestCase):

    def test_no_revisions_posted(self):
        """If user has no revisions, it should be stated in summary template."""
        # The expected text

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        resp = self.client.post(full_ban_url)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        revisions_submitted_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted_section = page.find('#revisions-reverted')
        revisions_deleted_section = page.find('#revisions-deleted')
        # TODO: Add in Phase IV
        # revisions_emailed_section = page.find('#revisions-emailed')
        revisions_submitted_as_spam_section = page.find('#revisions-followup')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), 0)
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), 0)
        eq_(len(revisions_submitted_as_spam), 0)

        expected_text = 'The user did not have any revisions that were reverted.'
        ok_(expected_text in revisions_reverted_section.text())
        expected_text = 'The user did not have any revisions that were deleted.'
        ok_(expected_text in revisions_deleted_section.text())
        expected_text = 'None.'
        # TODO: Add in Phase IV
        # ok_(expected_text in revisions_emailed_section.text())
        ok_(expected_text in revisions_submitted_as_spam_section.text())

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        eq_(len(not_spam), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_revisions_posted_different_docs(self, mock_form):
        """If user has made revisions and reviewer checked them to be reverted."""
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

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reported_as_spam_text = ''
        for rev in revisions_reported_as_spam:
            revisions_reported_as_spam_text += rev.text_content()
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), len(revisions_created))
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), len(revisions_created))
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), len(revisions_created))
        # The title for each of the created revisions shows up in the template
        for revision in revisions_created:
            ok_(revision.title in revisions_reported_as_spam_text)
        # The title for the original revision is not in the template
        ok_(self.original_revision.title not in revisions_reported_as_spam_text)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        eq_(len(not_spam), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_revisions_posted_same_doc(self, mock_form):
        """Only 1 revision per document should be shown on the summary page."""
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
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

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 1)
        eq_(len(revisions_reverted), 1)
        eq_(len(revisions_deleted), 0)
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), 1)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        eq_(len(not_spam), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_revisions_not_submitted_to_akismet(self, mock_form):
        """If revision not submitted to Akismet, summary template states this."""
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

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        # TODO: Add in Phase III
        # revisions_reverted = page.find('#revisions-reverted li')
        # revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 0)
        # TODO: Add in Phase III
        # eq_(len(revisions_reverted), 1)
        # eq_(len(revisions_deleted), 0)
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), 1)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        # TODO: Add in Phase III
        # could_not_delete = page.find('#could-not-delete li')
        # could_not_revert = page.find('#could-not-revert li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 3)
        # TODO: Add in Phase III
        # eq_(len(could_not_delete), 0)
        # eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        eq_(len(not_spam), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_no_revision_ids_posted(self, mock_form):
        """POSTing without checking any revisions as spam."""
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)
        # Create a revision on a new document
        self.create_revisions(
            num=1,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': []}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        # TODO: Add in Phase III
        # revisions_reverted = page.find('#revisions-reverted li')
        # revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 0)
        # TODO: Add in Phase III
        # eq_(len(revisions_reverted), 1)
        # eq_(len(revisions_deleted), 0)
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), 1)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        # TODO: Add in Phase III
        # could_not_delete = page.find('#could-not-delete li')
        # could_not_revert = page.find('#could-not-revert li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        # Since no ids were posted nothing should have been submitted to Akismet
        eq_(len(not_submitted_to_akismet), 0)
        # TODO: Add in Phase III
        # eq_(len(could_not_delete), 0)
        # eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        # The latest revision from each of the two documents should show up as 'not spam'
        eq_(len(not_spam), 2)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_all_revisions_already_spam(self, mock_form):
        """POSTing with all of user's revisions being marked as already spam."""
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        revisions_created_self_document = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)
        # Create a revision on a new document
        revisions_created_new_document = self.create_revisions(
            num=1,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        revisions_created_ids = [rev.id for rev in revisions_created_self_document] + [rev.id for rev in revisions_created_new_document]
        data = {'revision-already-spam': revisions_created_ids}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        # TODO: Add in Phase III
        # revisions_reverted = page.find('#revisions-reverted li')
        # revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 0)
        # TODO: Add in Phase III
        # eq_(len(revisions_reverted), 1)
        # eq_(len(revisions_deleted), 0)
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), 1)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        # TODO: Add in Phase III
        # could_not_delete = page.find('#could-not-delete li')
        # could_not_revert = page.find('#could-not-revert li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        # There were no errors submitting to Akismet, so no follow up is needed
        eq_(len(not_submitted_to_akismet), 0)
        # TODO: Add in Phase III
        # eq_(len(could_not_delete), 0)
        # eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        # One revision should show up for each of the documents
        eq_(len(already_spam), 2)
        eq_(len(not_spam), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_some_revision_ids_posted(self, mock_form):
        """POSTing having marked only some revisions as spam."""
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True

        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        revs_doc_1 = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)
        # Create a new document and 3 revisions on it
        doc1 = create_document(save=True)
        revs_doc_1 = self.create_revisions(
            num=3,
            document=doc1,
            creator=self.testuser)
        # Create another new document and 3 revisions on it
        doc2 = create_document(save=True)
        revs_doc_2 = self.create_revisions(
            num=3,
            document=doc2,
            creator=self.testuser)
        # Create yet another new document and 3 revisions on it
        doc3 = create_document(save=True)
        revs_doc_3 = self.create_revisions(
            num=3,
            document=doc3,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        # POST no revisions from self.document, the 1st from doc1,
        # the 1st and 2nd revisions from doc2, and all revisions from doc 3
        posted_ids = [
            revs_doc_1[0].id,
            revs_doc_2[0].id, revs_doc_2[1].id,
            revs_doc_3[0].id, revs_doc_3[1].id, revs_doc_3[2].id
        ]
        data = {'revision-id': posted_ids}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        # TODO: Add in Phase III
        # revisions_reverted = page.find('#revisions-reverted li')
        # revisions_deleted= page.find('#revisions-deleted li')
        # TODO: Add in Phase IV
        # revisions_emailed= page.find('#revisions-emailed li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 3)
        # The revisions shown are revs_doc_1[0], revs_doc_2[1], and revs_doc_3[2]
        for item in revisions_reported_as_spam:
            # Verify that the revision title matches what we're looking for
            ok_(item.text_content().strip() in [revs_doc_1[0].title, revs_doc_2[1].title, revs_doc_3[2].title])
        # TODO: Add in Phase III
        # eq_(len(revisions_reverted), 1)
        # eq_(len(revisions_deleted), 0)
        # TODO: Add in Phase IV
        # eq_(len(revisions_emailed), 1)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        # TODO: Add in Phase III
        # could_not_delete = page.find('#could-not-delete li')
        # could_not_revert = page.find('#could-not-revert li')
        # TODO: Add in Phase IV
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        # TODO: Add in Phase III
        # eq_(len(could_not_delete), 0)
        # eq_(len(could_not_revert), 0)
        # TODO: Add in Phase IV
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        # Revisions from self.document, doc1, and doc2 should be considered 'not spam'
        eq_(len(not_spam), 3)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_delete_link_appears_summary_page(self, mock_form):
        """
        Delete link should appear on the summary page sometimes.

        This should occur if: 1.) The user created the document and
        2.) the document has no other revision.
        The places in the template where this link may occur are:
        1.) Reverted or 2.) New action by user or 3.) Already identified as spam.
        Check all of these places in this test.
        """
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True
        # Create an original revision on a document by the self.testuser
        doc1 = create_document(save=True)
        rev_doc1 = create_revision(
            title='Revision 0',
            document=doc1,
            creator=self.testuser,
            save=True)
        # Create an original revision on another document by the self.testuser
        doc2 = create_document(save=True)
        rev_doc2 = create_revision(
            title='Revision 0',
            document=doc2,
            creator=self.testuser,
            save=True)

        # TODO: Phase IV: create a revision that will go into the "New action by user" section

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev_doc1.id], 'revision-already-spam': [rev_doc2.id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # TODO: PhaseIII: The revision on doc1 should have a delete link in the
        # "Reverted" section under "Actions taken"
        # doc1_delete_url = reverse(
        #     'wiki.delete_document',
        #     kwargs={'document_path': doc1.slug},
        #     force_locale=True)
        # doc1_delete_link = page.find('#reverted a[href="{url}"]'.format(
        #     url=doc1_delete_url))
        # TODO: PhaseIV: The revision done after the reviewing has begun should
        # have a delete link in the "New action by user" section under "Needs follow up"

        # The revision on doc2 should have a delete link in the "Already identified as spam"
        # section under "No actions taken"
        doc2_delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': doc2.slug},
            force_locale=True)
        doc2_delete_link = page.find('#already-spam a[href="{url}"]'.format(
            url=doc2_delete_url))

        # There should be 1 delete link found in each section
        # TODO: PhaseIII
        # eq_(len(doc1_delete_link), 1)
        eq_(len(doc2_delete_link), 1)
        # TODO: PhaseIV
        # eq_(len(doc3_delete_link), 1)

    def test_delete_link_does_not_appear_summary_page_no_create_doc(self):
        """
        Delete link should not appear on summary page sometimes.

        This should occur if: 1.) The user did not create the document or
        2.) the document has other revisions.
        This test goes through situation 1.)

        The places in the template where this link may occur are:
        1.) Reverted or 2.) New action by user or 3.) Already identified as spam.
        Check all of these places in this test.
        """
        # User makes a revision on another user's document
        revisions_already_spam = self.create_revisions(
            num=1,
            document=self.document,
            creator=self.testuser)
        # TODO: PhaseIII
        # Create another doc and a revision by self.admin and a revision by self.testuser
        # new_doc = create_document(save=True)
        # self.create_revisions(
        #     num=1,
        #     document=new_doc,
        #     creator=self.admin)
        # revisions_reverted = self.create_revisions(
        #     num=1,
        #     document=new_doc,
        #     creator=self.testuser)
        # TODO: PhaseIV: Create a revision by self.testuser after reviewing has
        # begun so it shows up in the "New action by user" section

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-already-spam': [revisions_already_spam[0].id]}
        # TODO: PhaseIII
        # data = {
        #     'revision-id': revisions_reverted[0].id,
        #     'revision-already-spam': [revisions_already_spam[0].id]
        # }
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': self.document.slug},
            force_locale=True)
        # TODO: PhaseIII
        # delete_link_reverted_section = page.find('#reverted a[href="{url}"]'.format(
        #     url=delete_url))
        # TODO: PhaseIV
        # delete_link_new_action_section = page.find('#new-actions-by-user a[href="{url}"]'.format(
        #     url=delete_url))
        delete_link_already_spam_section = page.find('#already-spam a[href="{url}"]'.format(
            url=delete_url))

        # There should not be a delete link in any of these sections
        # TODO: PhaseIII
        # eq_(len(delete_link_reverted_section), 0)
        # TODO: PhaseIV
        # eq_(len(delete_link_new_action_section), 0)
        eq_(len(delete_link_already_spam_section), 0)

    def test_delete_link_does_not_appear_summary_page_other_revisions(self):
        """
        Delete link should not appear on summary page sometimes.

        This should occur if:
        1.) The user did not create the document or
        2.) the document has other revisions.
        This test goes through situation 2.)

        The places in the template where this link may occur are:
        1.) Reverted or 2.) New action by user or 3.) Already identified as spam.
        Check all of these places in this test.
        """
        # User creates a document, but another user makes a revision on it
        doc1 = create_document(save=True)
        testuser_revisions = self.create_revisions(
            num=1,
            document=doc1,
            creator=self.testuser)
        create_revision(
            title='Revision 1',
            document=doc1,
            creator=self.testuser2,
            save=True)

        # User creates another document, but another user makes a revision on it
        doc2 = create_document(save=True)
        testuser_revisions = self.create_revisions(
            num=1,
            document=doc2,
            creator=self.testuser)
        create_revision(
            title='Revision 1',
            document=doc2,
            creator=self.testuser2,
            save=True)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-already-spam': [testuser_revisions[0].id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        delete_url_already_spam = reverse(
            'wiki.delete_document',
            kwargs={'document_path': doc1.slug},
            force_locale=True)

        delete_url_reverted = reverse(
            'wiki.delete_document',
            kwargs={'document_path': doc2.slug},
            force_locale=True)
        # TODO: PhaseIV
        # delete_url_new_action

        delete_link_reverted_section = page.find('#reverted a[href="{url}"]'.format(
            url=delete_url_reverted))
        # TODO: PhaseIV
        # delete_link_new_action_section = page.find('#new-actions-by-user a[href="{url}"]'.format(
        #     url=delete_url_new_action))
        delete_link_already_spam_section = page.find('#already-spam a[href="{url}"]'.format(
            url=delete_url_already_spam))

        # There should not be a delete link in any of these sections
        eq_(len(delete_link_reverted_section), 0)
        # TODO: PhaseIV
        # eq_(len(delete_link_new_action_section), 0)
        eq_(len(delete_link_already_spam_section), 0)

    def test_newest_revision_is_not_spam(self):
        """
        Test with a spam user who has made revisions to a single document,
        but another user has made a more recent revision.
        The newest revision was created by a non-spam user,
        so none of the revisions actually need to be reverted.
        """
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        spam_revisions = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)
        self.create_revisions(
            num=1,
            document=self.document,
            creator=self.admin)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_needing_follow_up = page.find('#manual-revert-needed li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # Because no revisions needed to be reverted, none need follow up
        eq_(len(revisions_needing_follow_up), 0)
        # Only one document is listed on the reported as spam list (distinct document)
        eq_(len(revisions_reported_as_spam), 1)

    def test_multiple_revisions_are_spam(self):
        """
        Test with a spam user who has made multiple revisions to a single document.
        This document should be reverted to the last version that was created
        by a non-spam user (self.admin).
        The newest revision was created by a non-spam user,
        so none of the revisions actually need to be reverted.
        """
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        self.create_revisions(
            num=1,
            document=self.document,
            creator=self.admin)
        spam_revisions = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'user_id': self.testuser.id})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        revisions_needing_follow_up = page.find('#manual-revert-needed li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # Because no revisions needed to be reverted, none need follow up
        eq_(len(revisions_needing_follow_up), 0)
        # Only one document is listed on the reported as spam list (distinct document)
        eq_(len(revisions_reported_as_spam), 1)


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
