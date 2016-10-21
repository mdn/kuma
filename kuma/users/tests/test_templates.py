import json
import pytest
from constance import config as constance_config
from constance.test.utils import override_config
from django.conf import settings
from mock import patch
from pyquery import PyQuery as pq
from waffle.models import Flag
from django.db import IntegrityError

from kuma.core.tests import eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.wiki.models import RevisionAkismetSubmission, DocumentDeletionLog, Document
from kuma.wiki.tests import document as create_document, revision as create_revision

from . import SampleRevisionsMixin, SocialTestMixin, UserTestCase
from .test_views import TESTUSER_PASSWORD
from ..models import User, UserBan


class SignupTests(UserTestCase, SocialTestMixin):
    localizing_client = False
    profile_create_strings = (
        'Create your MDN profile to continue',
        'choose a username',
        'having trouble',
        'I agree',
        'to Mozilla',
        'Terms',
        'Privacy Notice')

    def test_signup_page_github(self):
        response = self.github_login()
        self.assertNotContains(response, 'Sign In Failure')
        for test_string in self.profile_create_strings:
            self.assertContains(response, test_string)
        session = response.context['request'].session
        self.assertIn('socialaccount_sociallogin', session)
        self.assertEqual(session['sociallogin_provider'], 'github')

    def test_signup_page_disabled(self):
        registration_disabled = Flag.objects.create(
            name='registration_disabled',
            everyone=True
        )
        response = self.github_login()
        self.assertNotContains(response, 'Sign In Failure')
        self.assertContains(response, 'Profile Creation Disabled')
        session = response.context['request'].session
        self.assertNotIn('socialaccount_sociallogin', session)
        self.assertNotIn('sociallogin_provider', session)

        # re-enable registration
        registration_disabled.everyone = False
        registration_disabled.save()
        response = self.github_login()
        test_strings = ['Create your MDN profile to continue',
                        'choose a username',
                        'having trouble']
        for test_string in test_strings:
            self.assertContains(response, test_string)
        session = response.context['request'].session
        self.assertIn('socialaccount_sociallogin', session)
        self.assertEqual(session['sociallogin_provider'], 'github')


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


class AllauthGitHubTestCase(UserTestCase, SocialTestMixin):
    existing_email = 'testuser@test.com'
    existing_username = 'testuser'
    localizing_client = False

    def test_auth_failure(self):
        """A failed GitHub auth shows the sign in failure page."""
        token_data = {
            'error': 'incorrect_client_credentials',
            'error_description': 'The client_id passed is incorrect.',
        }
        response = self.github_login(token_data=token_data)
        assert response.status_code == 200
        content = response.content
        assert 'Account Sign In Failure' in content
        error = ('An error occurred while attempting to sign in with your'
                 ' account.')
        assert error in content
        assert 'Thanks for signing in to MDN' not in content

    def test_auth_success_username_available(self):
        """Successful auth shows profile creation with GitHub details."""
        response = self.github_login()
        assert response.status_code == 200
        content = response.content
        assert 'Thanks for signing in to MDN with GitHub.' in content
        assert 'Account Sign In Failure' not in content

        parsed = pq(response.content)
        username = parsed('#id_username')[0]
        assert username.value == self.github_profile_data['login']
        email0 = parsed('#email_0')[0].attrib['value']
        assert email0 == self.github_email_data[0]['email']
        email1 = parsed('#email_1')[0].attrib['value']
        assert email1 == self.github_profile_data['email']

    def test_signin(self):
        """Successful auth to existing account is reflected in tools."""
        user = User.objects.get(username=self.existing_username)
        user.socialaccount_set.create(provider='github',
                                      uid=self.github_token_data['uid'])
        profile_data = self.github_profile_data.copy()
        profile_data['login'] = self.existing_username
        profile_data['email'] = self.existing_email
        response = self.github_login(profile_data=profile_data)
        assert response.status_code == 200

        locale = settings.WIKI_DEFAULT_LANGUAGE
        user_url = reverse('users.user_detail',
                           kwargs={'username': self.existing_username},
                           locale=locale)
        logout_url = reverse('account_logout', locale=locale)
        home_url = reverse('home', locale=locale)
        signout_url = urlparams(logout_url, next=home_url)
        parsed = pq(response.content)

        login_info = parsed.find('.login')
        user_link, signout_link = login_info.children()
        assert user_link.attrib['href'] == user_url
        expected = signout_url.replace('%2F', '/')  # decode slashes
        assert signout_link.attrib['href'] == expected

    def test_signin_form_present(self):
        """When not authenticated, the GitHub login link is present."""
        locale = settings.WIKI_DEFAULT_LANGUAGE
        all_docs_url = reverse('wiki.all_documents', locale=locale)
        response = self.client.get(all_docs_url, follow=True)
        parsed = pq(response.content)
        github_link = parsed.find("a.login-link[data-service='GitHub']")[0]
        github_url = urlparams(reverse('github_login'),
                               next=all_docs_url)
        assert github_link.attrib['href'] == github_url

    def test_signup(self):
        """
        After a new user signs up with Persona, their username, an
        indication that Persona was used to log in, and a logout link
        appear in the auth tools section of the page.
        """
        response = self.github_login()
        assert response.status_code == 200
        assert 'Sign In Failure' not in response.content

        username = self.github_profile_data['login']
        email = self.github_email_data[0]['email']
        data = {'website': '',
                'username': username,
                'email': email,
                'terms': True}
        locale = settings.WIKI_DEFAULT_LANGUAGE
        signup_url = reverse('socialaccount_signup', locale=locale)
        response = self.client.post(signup_url, data=data, follow=True)
        assert response.status_code == 200

        user_url = reverse('users.user_detail',
                           kwargs={'username': username},
                           locale=locale)
        logout_url = reverse('account_logout', locale=locale)
        home_url = reverse('home', locale=locale)
        signout_url = urlparams(logout_url, next=home_url)
        parsed = pq(response.content)

        login_info = parsed.find('.login')
        user_link, signout_link = login_info.children()
        assert user_link.attrib['href'] == user_url
        expected = signout_url.replace('%2F', '/')
        assert signout_link.attrib['href'] == expected


@pytest.mark.bans
class BanTestCase(UserTestCase):

    def test_common_reasons_in_template(self):
        # The common reasons to ban users (from constance) should be in template
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

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
                          kwargs={'username': testuser.username})

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
                          kwargs={'username': testuser.username})

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
                          kwargs={'username': self.testuser.username})

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
                          kwargs={'username': self.testuser.username})

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
                          kwargs={'username': self.testuser.username})

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
                          kwargs={'username': self.testuser.username})
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
                          kwargs={'username': self.testuser2.username})
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
                          kwargs={'username': self.testuser.username})

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
                          kwargs={'username': self.testuser2.username})

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
                          kwargs={'username': self.testuser2.username})
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
        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        resp = self.client.post(full_ban_url)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        revisions_submitted_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted_section = page.find('#revisions-reverted')
        revisions_deleted_section = page.find('#revisions-deleted')
        revisions_submitted_as_spam_section = page.find('#revisions-followup')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), 0)
        eq_(len(revisions_submitted_as_spam), 0)

        expected_text = 'The user did not have any revisions that were reverted.'
        ok_(expected_text in revisions_reverted_section.text())
        expected_text = 'The user did not have any revisions that were deleted.'
        ok_(expected_text in revisions_deleted_section.text())
        expected_text = 'None.'
        ok_(expected_text in revisions_submitted_as_spam_section.text())

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
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
                          kwargs={'username': self.testuser.username})
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
        revisions_deleted = page.find('#revisions-deleted li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), len(revisions_created))
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), len(revisions_created))
        # The title for each of the created revisions shows up in the template
        for revision in revisions_created:
            ok_(revision.title in revisions_reported_as_spam_text)
        # The title for the original revision is not in the template
        ok_(self.original_revision.title not in revisions_reported_as_spam_text)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
        # eq_(len(new_actions), 0)

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        eq_(len(already_spam), 0)
        eq_(len(not_spam), 0)

    @patch('kuma.wiki.forms.RevisionAkismetSubmissionSpamForm.is_valid')
    def test_revisions_posted_same_doc(self, mock_form):
        """
        Only 1 revision per document should be shown on the summary page.  All
        revisions here are spam except for the original, so this document will
        be reverted.
        """
        # Mock the RevisionAkismetSubmissionSpamForm.is_valid() method
        mock_form.return_value = True
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        revisions_created = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 1)
        eq_(len(revisions_reverted), 1)
        eq_(len(revisions_deleted), 0)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')

        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
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
        revisions_created = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 0)
        eq_(len(revisions_reverted), 1)
        eq_(len(revisions_deleted), 0)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 1)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
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
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': []}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 0)
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), 0)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        # Since no ids were posted nothing should have been submitted to Akismet
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
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
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        revisions_created_ids = [
            rev.id for rev in revisions_created_self_document
        ] + [
            rev.id for rev in revisions_created_new_document
        ]
        data = {'revision-already-spam': revisions_created_ids}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 0)
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), 0)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        # There were no errors submitting to Akismet, so no follow up is needed
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
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
        self.create_revisions(
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
        # this new doc should be deleted when we send in all revisions.
        doc3 = create_document(save=True)
        revs_doc_3 = self.create_revisions(
            num=3,
            document=doc3,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        # POST no revisions from self.document, the 1st from doc1,
        # the 1st and 2nd revisions from doc2, and all revisions from doc 3
        # doc 1 and doc 2 should have no action (newest revision is unchecked)
        # doc 3 should be deleted
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
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        eq_(banned_user, self.testuser.username)
        eq_(len(revisions_reported_as_spam), 3)
        # The revisions shown are revs_doc_1[0], revs_doc_2[1], and revs_doc_3[2]
        for item in revisions_reported_as_spam:
            # Verify that the revision title matches what we're looking for
            ok_(item.text_content().strip() in [revs_doc_1[0].title, revs_doc_2[1].title, revs_doc_3[2].title])
        eq_(len(revisions_reverted), 0)
        eq_(len(revisions_deleted), 1)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        eq_(len(not_submitted_to_akismet), 0)
        eq_(len(could_not_delete), 0)
        eq_(len(could_not_revert), 0)
        # TODO: Add in Phase V
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
        # TODO: Phase V: arrange that this revision will go into the "New action by user"
        # section.  Currently the document will wind up being deleted automatically.

        # Create an original revision on another document by the self.testuser
        doc2 = create_document(save=True)
        rev_doc2 = create_revision(
            title='Revision 0',
            document=doc2,
            creator=self.testuser,
            save=True)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev_doc1.id], 'revision-already-spam': [rev_doc2.id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # TODO: Phase V: The revision done after the reviewing has begun should
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
        # TODO: Phase V
        # eq_(len(doc1_delete_link), 1)
        eq_(len(doc2_delete_link), 1)

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

        # TODO: Phase V: Create a revision by self.testuser after reviewing has
        # begun so it shows up in the "New action by user" section

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-already-spam': [revisions_already_spam[0].id]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': self.document.slug},
            force_locale=True)
        # TODO: PhaseV
        # delete_link_new_action_section = page.find('#new-actions-by-user a[href="{url}"]'.format(
        #     url=delete_url))
        delete_link_already_spam_section = page.find('#already-spam a[href="{url}"]'.format(
            url=delete_url))

        # There should not be a delete link in any of these sections
        # TODO: PhaseV
        # eq_(len(delete_link_new_action_section), 0)
        eq_(len(delete_link_already_spam_section), 0)

    def test_delete_link_does_not_appear_summary_page_other_revisions(self):
        """
        Delete link should not appear on summary page sometimes.

        This should occur if: 1.) The user did not create the document or
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
                          kwargs={'username': self.testuser.username})
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
        # TODO: PhaseV
        # delete_url_new_action

        delete_link_reverted_section = page.find('#reverted a[href="{url}"]'.format(
            url=delete_url_reverted))
        # TODO: PhaseV
        # delete_link_new_action_section = page.find('#new-actions-by-user a[href="{url}"]'.format(
        #     url=delete_url_new_action))
        delete_link_already_spam_section = page.find('#already-spam a[href="{url}"]'.format(
            url=delete_url_already_spam))

        # There should not be a delete link in any of these sections
        eq_(len(delete_link_reverted_section), 0)
        # TODO: PhaseV
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
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # No new documents by the spammer, so none deleted
        eq_(len(revisions_deleted), 0)
        # Document was not reverted, since there was a newer non-spam rev
        eq_(len(revisions_reverted), 0)

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # No new revs were added by the user while we were working
        eq_(len(revisions_added_afterwards), 0)
        # One document had revisions that were ignored, because there was a newer good rev
        eq_(len(revisions_skipped), 1)
        # Only one document is listed on the reported as spam list (distinct document)
        eq_(len(revisions_reported_as_spam), 1)

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # The only document was left unreverted due to having a good rev for its latest
        eq_(len(revisions_not_reverted), 1)
        # No documents had revs that were already marked as spam
        eq_(len(revisions_already_spam), 0)
        # No documents had revs that were unchecked in the spam form
        eq_(len(revisions_not_spam), 0)

    def test_intermediate_non_spam_rev(self):
        """
        Test with a spam user who has made revisions to a single document,
        but another user has made a revision in between those.
        """
        # Create two spam revisions, with one good revision in between.
        bottom_spam = self.create_revisions(
            num=1,
            document=self.document,
            creator=self.testuser)
        self.create_revisions(
            num=1,
            document=self.document,
            creator=self.admin)
        top_spam = self.create_revisions(
            num=1,
            document=self.document,
            creator=self.testuser)
        spam_revisions = bottom_spam + top_spam

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # No new documents by the spammer, so none deleted
        eq_(len(revisions_deleted), 0)
        # Only one set of reverted revisions
        eq_(len(revisions_reverted), 1)

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # No new revs were added by the user while we were working
        eq_(len(revisions_added_afterwards), 0)
        # One document had revisions that were ignored, because there was a newer good rev
        eq_(len(revisions_skipped), 1)
        # Only one document is listed on the reported as spam list (distinct document)
        eq_(len(revisions_reported_as_spam), 1)

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No documents were left unreverted due to having a good rev for its latest
        eq_(len(revisions_not_reverted), 0)
        # No documents had revs that were already marked as spam
        eq_(len(revisions_already_spam), 0)
        # No documents had revs that were unchecked in the spam form
        eq_(len(revisions_not_spam), 0)

    def test_multiple_revisions_are_spam(self):
        """
        Test with a spam user who has made multiple revisions to a single
        document.  This document should be reverted to the last version that was
        created by a non-spam user (self.admin).

        The original revision was created by the admin and then three more were
        created by the spammer, with no addition revisions afterwards, so we
        should wind up reverting to the original revision.

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
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(full_ban_url, data=data)
        eq_(200, resp.status_code)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # No new documents by the spammer, so none deleted
        eq_(len(revisions_deleted), 0)
        # Only one set of reverted revisions
        eq_(len(revisions_reverted), 1)

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # To be implemented in Phase V
        eq_(len(revisions_added_afterwards), 0)
        # All of the spam revisions were covered by the reversion
        eq_(len(revisions_skipped), 0)
        # Only one document is listed on the reported as spam list (distinct document)
        eq_(len(revisions_reported_as_spam), 1)

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No documents were left unreverted due to having a good rev for its latest
        eq_(len(revisions_not_reverted), 0)
        # No documents had revs that were already marked as spam
        eq_(len(revisions_already_spam), 0)
        # No documents had revs that were unchecked in the spam form
        eq_(len(revisions_not_spam), 0)

    def test_delete_document_failure(self):
        # Create a new spam document with a single revision
        spam_revision = self.create_revisions(
            num=1,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        with patch.object(DocumentDeletionLog.objects, 'create') as dl_mock:
            # Just raise an IntegrityError to get delete_document to fail
            dl_mock.side_effect = IntegrityError()

            data = {'revision-id': [rev.id for rev in spam_revision]}
            resp = self.client.post(full_ban_url, data=data)

        eq_(200, resp.status_code)
        page = pq(resp.content)

        eq_(DocumentDeletionLog.objects.count(), 0)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # The document failed to be deleted
        eq_(len(revisions_deleted), 0)
        # It wouldn't have been reverted anyway
        eq_(len(revisions_reverted), 0)

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')

        # To be implemented in Phase V
        eq_(len(revisions_added_afterwards), 0)
        # Nothing happened
        eq_(len(revisions_skipped), 0)
        # Akismet reporting happens first
        eq_(len(revisions_reported_as_spam), 1)
        # The deletion failed, so it goes here
        eq_(len(could_not_delete), 1)
        eq_(len(could_not_revert), 0)

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No good revisions superceding bad ones
        eq_(len(revisions_not_reverted), 0)
        # No documents had revs that were already marked as spam
        eq_(len(revisions_already_spam), 0)
        # No documents had revs that were unchecked in the spam form
        eq_(len(revisions_not_spam), 0)

    def test_revert_document_failure(self):
        # Create some spam revisions on a previously good document.
        spam_revisions = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        full_ban_url = self.client.get(ban_url)['Location']

        with patch.object(Document, 'revert') as revert_mock:
            # Just raise an IntegrityError to get revert_document to fail
            revert_mock.side_effect = IntegrityError()

            data = {'revision-id': [rev.id for rev in spam_revisions]}
            resp = self.client.post(full_ban_url, data=data)

        eq_(200, resp.status_code)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # The document wouldn't have been deleted
        eq_(len(revisions_deleted), 0)
        # It failed to be reverted
        eq_(len(revisions_reverted), 0)

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')

        # To be implemented in Phase V
        eq_(len(revisions_added_afterwards), 0)
        # Nothing happened
        eq_(len(revisions_skipped), 0)
        # Akismet reporting happens first
        eq_(len(revisions_reported_as_spam), 1)
        eq_(len(could_not_delete), 0)
        # The revert failed, so it goes here
        eq_(len(could_not_revert), 1)

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No good revisions superceding bad ones
        eq_(len(revisions_not_reverted), 0)
        # No documents had revs that were already marked as spam
        eq_(len(revisions_already_spam), 0)
        # No documents had revs that were unchecked in the spam form
        eq_(len(revisions_not_spam), 0)


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
