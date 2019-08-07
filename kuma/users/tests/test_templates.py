import json

import pytest
from allauth.account.models import EmailAddress
from constance import config as constance_config
from constance.test.utils import override_config
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse
from mock import patch
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.wiki.models import Document, DocumentDeletionLog
from kuma.wiki.tests import (document as create_document,
                             revision as create_revision)

from . import SampleRevisionsMixin, SocialTestMixin, UserTestCase
from ..models import User, UserBan


class SignupTests(UserTestCase, SocialTestMixin):
    profile_create_strings = (
        'Create your MDN profile',
        'choose a username',
        'Have trouble',
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
        with override_switch('registration_disabled', True):
            response = self.github_login()
        self.assertNotContains(response, 'Sign In Failure')
        self.assertContains(response, 'Profile Creation Disabled')
        session = response.context['request'].session
        self.assertNotIn('socialaccount_sociallogin', session)
        self.assertNotIn('sociallogin_provider', session)

        # re-enable registration
        with override_switch('registration_disabled', False):
            response = self.github_login()
        test_strings = ['Create your MDN profile',
                        'choose a username',
                        'Have trouble']
        for test_string in test_strings:
            self.assertContains(response, test_string)
        session = response.context['request'].session
        self.assertIn('socialaccount_sociallogin', session)
        self.assertEqual(session['sociallogin_provider'], 'github')


def test_account_email_page_requires_signin(db, client):
    response = client.get(reverse('account_email'))
    assert response.status_code == 302
    assert_no_cache_header(response)
    response = client.get(response['Location'], follow=True)
    assert response.status_code == 200
    assert b'Please sign in' in response.content


def test_account_email_page_single_email(user_client):
    response = user_client.get(reverse('account_email'))
    assert response.status_code == 200
    assert_no_cache_header(response)
    content = response.content.decode(response.charset)
    assert 'is your <em>primary</em> email address' in content
    assert 'Make Primary' not in content
    assert 'Re-send Confirmation' not in content
    assert 'Remove' not in content


def test_account_email_page_multiple_emails(wiki_user, user_client):
    EmailAddress.objects.create(user=wiki_user, email='wiki_user@backup.com',
                                verified=True, primary=False)
    response = user_client.get(reverse('account_email'))
    assert response.status_code == 200
    assert_no_cache_header(response)
    content = response.content.decode(response.charset)
    assert 'Make Primary' in content
    assert 'Re-send Confirmation' in content
    assert 'Remove' in content
    assert 'Add Email' in content
    assert 'Edit profile' in content


class AllauthGitHubTestCase(UserTestCase, SocialTestMixin):
    existing_email = 'testuser@test.com'
    existing_username = 'testuser'

    def test_auth_failure(self):
        """A failed GitHub auth shows the sign in failure page."""
        token_data = {
            'error': 'incorrect_client_credentials',
            'error_description': 'The client_id passed is incorrect.',
        }
        response = self.github_login(token_data=token_data)
        assert response.status_code == 200
        content = response.content
        assert b'Account Sign In Failure' in content
        error = (b'An error occurred while attempting to sign in with your'
                 b' account.')
        assert error in content
        assert b'Thanks for signing in to MDN' not in content

    def test_auth_success_username_available(self):
        """Successful auth shows profile creation with GitHub details."""
        response = self.github_login()
        assert response.status_code == 200
        content = response.content
        assert b'Thanks for signing in to MDN with GitHub.' in content
        assert b'Account Sign In Failure' not in content

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

        # The "github_login" method mocks requests, so when the "render_react"
        # call is made for the home page, it'll fail because there's no mock
        # address defined for that SSR request. For the purpose of this test,
        # we don't care about the content of the home page, so let's explicitly
        # mock the "render_home" call.
        with patch('kuma.landing.views.render_home') as mock_render_home:
            mock_render_home.return_value = HttpResponse()
            response = self.github_login(profile_data=profile_data)
        assert response.status_code == 200

    def test_signin_form_present(self):
        """When not authenticated, the GitHub login link is present."""
        all_docs_url = reverse('wiki.all_documents')
        response = self.client.get(all_docs_url, follow=True)
        parsed = pq(response.content)
        github_link = parsed.find("a.login-link[data-service='GitHub']")[0]
        github_url = urlparams(reverse('github_login'),
                               next=all_docs_url)
        assert github_link.attrib['href'] == github_url

    def test_signup(self):
        """
        After a new user logs in with GitHub, they signup to pick a username
        and email to use on MDN. Once signup is complete, the sign-in
        link is replaced by the profile and logout links.
        """
        response = self.github_login()
        assert response.status_code == 200
        assert 'Sign In Failure' not in response.content.decode('utf-8')

        # Test the signup form and our very custom email selector
        signup_url = reverse('socialaccount_signup')
        response = self.client.get(signup_url)
        parsed = pq(response.content)
        expected_emails = [
            {
                'li_attrib': {},
                'label_attrib': {'for': 'email_0'},
                'radio_attrib': {'required': '',
                                 'type': 'radio',
                                 'name': 'email',
                                 'value': 'octocat-private@example.com',
                                 'id': 'email_0'},
                'verified': True,
            }, {
                'li_attrib': {},
                'label_attrib': {'for': 'email_1'},
                'radio_attrib': {'checked': 'checked',
                                 'required': '',
                                 'type': 'radio',
                                 'name': 'email',
                                 'value': 'octocat@example.com',
                                 'id': 'email_1'},
                'verified': False,
            }, {
                'li_attrib': {},
                'label_attrib': {'class': 'inner other-label',
                                 'for': 'email_2'},
                'radio_attrib': {'required': '',
                                 'type': 'radio',
                                 'name': 'email',
                                 'value': '_other',
                                 'id': 'email_2'},
                'other_attrib': {'type': 'email',
                                 'name': 'other_email',
                                 'id': 'id_other_email'}
            },
        ]
        email_lis = parsed.find('ul.choices li')
        assert len(email_lis) == len(expected_emails)
        for expected, email_li in zip(expected_emails, email_lis):
            actual = {'li_attrib': email_li.attrib}
            email_label = email_li.find('label')
            actual['label_attrib'] = email_label.attrib
            email_inner = email_li.cssselect('input[type=email]')
            if email_inner:
                # The "Other:" element is arranged differently, has an email input
                actual['other_attrib'] = email_inner[0].attrib
                email_radio = email_li.cssselect('input[type=radio]')[0]
            else:
                # Standard selections from Github include if the email is verified
                text = email_label.text_content()
                actual['verified'] = 'Unknown'
                if 'Verified' in text:
                    actual['verified'] = True
                elif 'Unverified' in text:  # pragma: no cover
                    actual['verified'] = False
                email_radio = email_label.cssselect('input[type=radio]')[0]
            actual['radio_attrib'] = email_radio.attrib
            assert actual == expected

        # POST user choices to complete signup
        username = self.github_profile_data['login']
        email = self.github_email_data[0]['email']
        data = {'website': '',
                'username': username,
                'email': email,
                'terms': True}
        response = self.client.post(signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        # The rest of this test simply gets and checks the wiki home page.
        response = self.client.get(response['Location'], follow=True,
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200

        user_url = reverse('users.user_detail', kwargs={'username': username})
        logout_url = reverse('account_logout')
        home_url = reverse('home')
        signout_url = urlparams(logout_url)
        parsed = pq(response.content)

        login_info = parsed.find('.login')
        # Check login user url is there
        user_link = login_info.children('.user-url')
        assert user_link.attr['href'] == user_url

        form = login_info.find('form')
        # There should be signout link in the form action
        expected = signout_url.replace('%2F', '/')  # decode slashes
        assert form.attr['action'] == expected
        assert form.attr['method'] == 'post'
        # Check next url is provided as input field
        next_input = form.children("input[name='next']")
        assert next_input.val() == home_url
        # Ensure CSRF protection has not been added, since it creates problems
        # when used with a CDN like CloudFront (see bugzilla #1456165).
        csrf_input = form.children("input[name='csrfmiddlewaretoken']")
        assert not csrf_input


@pytest.mark.bans
class BanTestCase(UserTestCase):

    def test_common_reasons_in_template(self):
        # The common reasons to ban users (from constance) should be in template
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        reasons_to_ban_found = page.find('.ban-common-reason')
        reasons_to_ban_expected = json.loads(
            constance_config.COMMON_REASONS_TO_BAN_USERS
        )

        assert len(reasons_to_ban_found) == len(reasons_to_ban_expected)
        for reason in reasons_to_ban_found:
            assert reason.text in reasons_to_ban_expected

    @override_config(COMMON_REASONS_TO_BAN_USERS='Not valid JSON')
    def test_common_reasons_error(self):
        # If there is an error in getting the common reasons from constance,
        # then 'Spam' should still show up in the template as the default
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        reasons_to_ban_found = page.find('.ban-common-reason')
        reasons_to_ban_expected = ['Spam']

        assert len(reasons_to_ban_found) == len(reasons_to_ban_expected)
        for reason in reasons_to_ban_found:
            assert reason.text in reasons_to_ban_expected

    @override_config(COMMON_REASONS_TO_BAN_USERS='[]')
    def test_common_reasons_empty(self):
        # If the list of common reasons to ban users in constance is empty,
        # then 'Spam' should still show up in the template as the default
        testuser = self.user_model.objects.get(username='testuser')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

        resp = self.client.get(ban_url, follow=True,
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        reasons_to_ban_found = page.find('.ban-common-reason')
        reasons_to_ban_expected = ['Spam']

        assert len(reasons_to_ban_found) == len(reasons_to_ban_expected)
        for reason in reasons_to_ban_found:
            assert reason.text in reasons_to_ban_expected


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

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        revisions_found_text = ''
        for rev in revisions_found:
            revisions_found_text += rev.text_content()

        assert len(revisions_found) == len(revisions_expected)
        # The title for each of the created revisions shows up in the template
        for revision in revisions_expected:
            assert revision.title in revisions_found_text
        # The original revision created by the admin user is not in the template
        assert self.original_revision.title not in revisions_found_text

    def test_no_user_revisions_in_one_click_page_template(self):
        """If the user has no revisions, it should be stated in the template."""
        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'username': self.testuser.username})

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        no_revisions = page.find('#ban-and-cleanup-form')

        assert len(revisions_found) == 0
        assert ("This user has not created any revisions "
                "in the past three days." in no_revisions.text())

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

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        assert len(revisions_found) == num_revisions
        assert ban_button.text() == "Ban User for Spam & Submit Spam"
        assert len(ban_other_reasons) == 1

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
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        assert len(revisions_found) == 0
        assert ban_button.text() == "Ban User for Spam"
        assert len(ban_other_reasons) == 0

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
            revision.akismet_submissions.create(sender=self.testuser2,
                                                type="spam")

        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'username': self.testuser2.username})
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        assert len(revisions_found) == 3
        assert ban_button.text() == "Ban User for Spam"
        assert len(ban_other_reasons) == 0

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

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        assert len(revisions_found) == num_revisions
        assert ban_button.text() == "Submit Spam"
        assert len(ban_other_reasons) == 0

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

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        assert len(revisions_found) == 0
        assert len(ban_button) == 0
        assert len(ban_other_reasons) == 0

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
            revision.akismet_submissions.create(sender=self.testuser2,
                                                type="spam")

        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'username': self.testuser2.username})
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        revisions_found = page.find('.dashboard-row')
        ban_button = page.find('#ban-and-cleanup-form button[type=submit]')
        ban_other_reasons = page.find('#ban-for-other-reasons')

        assert len(revisions_found) == 3
        assert len(ban_button) == 0
        assert len(ban_other_reasons) == 0


@pytest.mark.bans
class BanUserAndCleanupSummaryTestCase(SampleRevisionsMixin, UserTestCase):

    def test_no_revisions_posted(self):
        """If user has no revisions, it should be stated in summary template."""
        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        resp = self.client.post(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        revisions_submitted_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted_section = page.find('#revisions-reverted')
        revisions_deleted_section = page.find('#revisions-deleted')
        revisions_submitted_as_spam_section = page.find('#revisions-followup')
        assert banned_user == self.testuser.username
        assert len(revisions_reverted) == 0
        assert len(revisions_deleted) == 0
        assert len(revisions_submitted_as_spam) == 0

        expected_text = 'The user did not have any revisions that were reverted.'
        assert expected_text in revisions_reverted_section.text()
        expected_text = 'The user did not have any revisions that were deleted.'
        assert expected_text in revisions_deleted_section.text()
        expected_text = 'None.'
        assert expected_text in revisions_submitted_as_spam_section.text()

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        assert len(not_submitted_to_akismet) == 0
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        assert len(already_spam) == 0
        assert len(not_spam) == 0

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
        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reported_as_spam_text = ''
        for rev in revisions_reported_as_spam:
            revisions_reported_as_spam_text += rev.text_content()
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        assert banned_user == self.testuser.username
        assert len(revisions_reported_as_spam) == len(revisions_created)
        assert len(revisions_reverted) == 0
        assert len(revisions_deleted) == len(revisions_created)
        # The title for each of the created revisions shows up in the template
        for revision in revisions_created:
            assert revision.title in revisions_reported_as_spam_text
        # The title for the original revision is not in the template
        assert (self.original_revision.title not in
                revisions_reported_as_spam_text)

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        assert len(not_submitted_to_akismet) == 0
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        assert len(already_spam) == 0
        assert len(not_spam) == 0

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
        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        assert banned_user == self.testuser.username
        assert len(revisions_reported_as_spam) == 1
        assert len(revisions_reverted) == 1
        assert len(revisions_deleted) == 0

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')

        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        assert len(not_submitted_to_akismet) == 0
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        assert len(already_spam) == 0
        assert len(not_spam) == 0

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
        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        assert banned_user == self.testuser.username
        assert len(revisions_reported_as_spam) == 0
        assert len(revisions_reverted) == 1
        assert len(revisions_deleted) == 0

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        assert len(not_submitted_to_akismet) == 1
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        assert len(already_spam) == 0
        assert len(not_spam) == 0

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
        data = {'revision-id': []}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        assert banned_user == self.testuser.username
        assert len(revisions_reported_as_spam) == 0
        assert len(revisions_reverted) == 0
        assert len(revisions_deleted) == 0

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        # Since no ids were posted nothing should have been submitted to Akismet
        assert len(not_submitted_to_akismet) == 0
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        assert len(already_spam) == 0
        # The latest revision from each of the two documents should show up as 'not spam'
        assert len(not_spam) == 2

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
        revisions_created_ids = [
            rev.id for rev in revisions_created_self_document
        ] + [
            rev.id for rev in revisions_created_new_document
        ]
        data = {'revision-already-spam': revisions_created_ids}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        assert banned_user == self.testuser.username
        assert len(revisions_reported_as_spam) == 0
        assert len(revisions_reverted) == 0
        assert len(revisions_deleted) == 0

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        # There were no errors submitting to Akismet, so no follow up is needed
        assert len(not_submitted_to_akismet) == 0
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        # One revision should show up for each of the documents
        assert len(already_spam) == 2
        assert len(not_spam) == 0

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
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # The "Actions taken" section
        banned_user = page.find('#banned-user li').text()
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        revisions_reverted = page.find('#revisions-reverted li')
        revisions_deleted = page.find('#revisions-deleted li')
        assert banned_user == self.testuser.username
        assert len(revisions_reported_as_spam) == 3
        # The revisions shown are revs_doc_1[0], revs_doc_2[1], and revs_doc_3[2]
        for item in revisions_reported_as_spam:
            # Verify that the revision title matches what we're looking for
            assert (item.text_content().strip() in
                    [revs_doc_1[0].title, revs_doc_2[1].title,
                     revs_doc_3[2].title])
        assert len(revisions_reverted) == 0
        assert len(revisions_deleted) == 1

        # The "Needs follow up" section
        not_submitted_to_akismet = page.find('#not-submitted-to-akismet li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')
        # TODO: Add in Phase V
        # new_actions = page.find('#new-actions-by-user li')
        assert len(not_submitted_to_akismet) == 0
        assert len(could_not_delete) == 0
        assert len(could_not_revert) == 0
        # TODO: Add in Phase V
        # assert len(new_actions) == 0

        # The "No actions taken" section
        already_spam = page.find('#already-spam li')
        not_spam = page.find('#not-spam li')
        assert len(already_spam) == 0
        # Revisions from self.document, doc1, and doc2 should be considered 'not spam'
        assert len(not_spam) == 3

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
        data = {'revision-id': [rev_doc1.id], 'revision-already-spam': [rev_doc2.id]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # TODO: Phase V: The revision done after the reviewing has begun should
        # have a delete link in the "New action by user" section under "Needs follow up"

        # The revision on doc2 should have a delete link in the "Already identified as spam"
        # section under "No actions taken"
        doc2_delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': doc2.slug})
        doc2_delete_link = page.find('#already-spam a[href="{url}"]'.format(
            url=doc2_delete_url))

        # There should be 1 delete link found in each section
        # TODO: Phase V
        # assert len(doc1_delete_link) == 1
        assert len(doc2_delete_link) == 1

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
        data = {'revision-already-spam': [revisions_already_spam[0].id]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        delete_url = reverse(
            'wiki.delete_document',
            kwargs={'document_path': self.document.slug})
        # TODO: PhaseV
        # delete_link_new_action_section = page.find('#new-actions-by-user a[href="{url}"]'.format(
        #     url=delete_url))
        delete_link_already_spam_section = page.find('#already-spam a[href="{url}"]'.format(
            url=delete_url))

        # There should not be a delete link in any of these sections
        # TODO: PhaseV
        # assert len(delete_link_new_action_section) == 0
        assert len(delete_link_already_spam_section) == 0

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
        data = {'revision-already-spam': [testuser_revisions[0].id]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        delete_url_already_spam = reverse(
            'wiki.delete_document',
            kwargs={'document_path': doc1.slug})
        delete_url_reverted = reverse(
            'wiki.delete_document',
            kwargs={'document_path': doc2.slug})
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
        assert len(delete_link_reverted_section) == 0
        # TODO: PhaseV
        # assert len(delete_link_new_action_section) == 0
        assert len(delete_link_already_spam_section) == 0

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
        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # No new documents by the spammer, so none deleted
        assert len(revisions_deleted) == 0
        # Document was not reverted, since there was a newer non-spam rev
        assert len(revisions_reverted) == 0

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # No new revs were added by the user while we were working
        assert len(revisions_added_afterwards) == 0
        # One document had revisions that were ignored, because there was a newer good rev
        assert len(revisions_skipped) == 1
        # Only one document is listed on the reported as spam list (distinct document)
        assert len(revisions_reported_as_spam) == 1

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # The only document was left unreverted due to having a good rev for its latest
        assert len(revisions_not_reverted) == 1
        # No documents had revs that were already marked as spam
        assert len(revisions_already_spam) == 0
        # No documents had revs that were unchecked in the spam form
        assert len(revisions_not_spam) == 0

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
        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # No new documents by the spammer, so none deleted
        assert len(revisions_deleted) == 0
        # Only one set of reverted revisions
        assert len(revisions_reverted) == 1

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # No new revs were added by the user while we were working
        assert len(revisions_added_afterwards) == 0
        # One document had revisions that were ignored, because there was a newer good rev
        assert len(revisions_skipped) == 1
        # Only one document is listed on the reported as spam list (distinct document)
        assert len(revisions_reported_as_spam) == 1

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No documents were left unreverted due to having a good rev for its latest
        assert len(revisions_not_reverted) == 0
        # No documents had revs that were already marked as spam
        assert len(revisions_already_spam) == 0
        # No documents had revs that were unchecked in the spam form
        assert len(revisions_not_spam) == 0

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
        data = {'revision-id': [rev.id for rev in spam_revisions]}
        resp = self.client.post(ban_url, data=data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # No new documents by the spammer, so none deleted
        assert len(revisions_deleted) == 0
        # Only one set of reverted revisions
        assert len(revisions_reverted) == 1

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')

        # To be implemented in Phase V
        assert len(revisions_added_afterwards) == 0
        # All of the spam revisions were covered by the reversion
        assert len(revisions_skipped) == 0
        # Only one document is listed on the reported as spam list (distinct document)
        assert len(revisions_reported_as_spam) == 1

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No documents were left unreverted due to having a good rev for its latest
        assert len(revisions_not_reverted) == 0
        # No documents had revs that were already marked as spam
        assert len(revisions_already_spam) == 0
        # No documents had revs that were unchecked in the spam form
        assert len(revisions_not_spam) == 0

    def test_delete_document_failure(self):
        # Create a new spam document with a single revision
        spam_revision = self.create_revisions(
            num=1,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        with patch.object(DocumentDeletionLog.objects, 'create') as dl_mock:
            # Just raise an IntegrityError to get delete_document to fail
            dl_mock.side_effect = IntegrityError()

            data = {'revision-id': [rev.id for rev in spam_revision]}
            resp = self.client.post(ban_url, data=data,
                                    HTTP_HOST=settings.WIKI_HOST)

        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        assert DocumentDeletionLog.objects.count() == 0

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # The document failed to be deleted
        assert len(revisions_deleted) == 0
        # It wouldn't have been reverted anyway
        assert len(revisions_reverted) == 0

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')

        # To be implemented in Phase V
        assert len(revisions_added_afterwards) == 0
        # Nothing happened
        assert len(revisions_skipped) == 0
        # Akismet reporting happens first
        assert len(revisions_reported_as_spam) == 1
        # The deletion failed, so it goes here
        assert len(could_not_delete) == 1
        assert len(could_not_revert) == 0

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No good revisions superceding bad ones
        assert len(revisions_not_reverted) == 0
        # No documents had revs that were already marked as spam
        assert len(revisions_already_spam) == 0
        # No documents had revs that were unchecked in the spam form
        assert len(revisions_not_spam) == 0

    def test_revert_document_failure(self):
        # Create some spam revisions on a previously good document.
        spam_revisions = self.create_revisions(
            num=3,
            document=self.document,
            creator=self.testuser)

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup_summary',
                          kwargs={'username': self.testuser.username})
        with patch.object(Document, 'revert') as revert_mock:
            # Just raise an IntegrityError to get revert_document to fail
            revert_mock.side_effect = IntegrityError()

            data = {'revision-id': [rev.id for rev in spam_revisions]}
            resp = self.client.post(ban_url, data=data,
                                    HTTP_HOST=settings.WIKI_HOST)

        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        # 'Actions taken' section

        revisions_deleted = page.find('#revisions-deleted li')
        revisions_reverted = page.find('#revisions-reverted li')

        # The document wouldn't have been deleted
        assert len(revisions_deleted) == 0
        # It failed to be reverted
        assert len(revisions_reverted) == 0

        # 'Needs follow-up' section

        revisions_added_afterwards = page.find('#new-actions-by-user li')
        revisions_skipped = page.find('#skipped-revisions li')
        revisions_reported_as_spam = page.find('#revisions-reported-as-spam li')
        could_not_delete = page.find('#not-deleted li')
        could_not_revert = page.find('#not-reverted li')

        # To be implemented in Phase V
        assert len(revisions_added_afterwards) == 0
        # Nothing happened
        assert len(revisions_skipped) == 0
        # Akismet reporting happens first
        assert len(revisions_reported_as_spam) == 1
        assert len(could_not_delete) == 0
        # The revert failed, so it goes here
        assert len(could_not_revert) == 1

        # 'No action' section

        revisions_not_reverted = page.find('#latest-revision-non-spam li')
        revisions_already_spam = page.find('#already-spam li')
        revisions_not_spam = page.find('#not-spam li')

        # No good revisions superceding bad ones
        assert len(revisions_not_reverted) == 0
        # No documents had revs that were already marked as spam
        assert len(revisions_already_spam) == 0
        # No documents had revs that were unchecked in the spam form
        assert len(revisions_not_spam) == 0


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
        resp = self.client.get(profile_url)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        ban_link = page.find('#ban_link')
        ban_cleanup_link = page.find('#cleanup_link')
        assert ban_link.text() == "Ban User"
        assert ban_cleanup_link.text() == "Ban User & Clean Up"

        # The user is banned, display appropriate links
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)
        resp = self.client.get(profile_url)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)

        ban_link = page.find('#ban_link')
        ban_cleanup_link = page.find('#cleanup_link')
        assert ban_link.text() == "Banned"
        assert ban_cleanup_link.text() == "Clean Up Revisions"

    def test_user_github_link(self):
        testuser = self.user_model.objects.get(username='testuser')
        assert not testuser.is_github_url_public

        profile_url = reverse('users.user_detail',
                              kwargs={'username': testuser.username})
        resp = self.client.get(profile_url)
        assert resp.status_code == 200
        assert_no_cache_header(resp)
        page = pq(resp.content)
        assert len(page.find('ul.user-links li.github')) == 0

        testuser.is_github_url_public = True
        testuser.save()
        resp = self.client.get(profile_url)
        assert resp.status_code == 200
        page = pq(resp.content)
        assert len(page.find('ul.user-links li.github')) == 1
