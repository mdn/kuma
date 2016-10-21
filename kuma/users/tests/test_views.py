import os
from textwrap import dedent

import mock
import pytest
import requests_mock
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from constance.test.utils import override_config
from django.conf import settings
from django.core import mail
from django.core.paginator import PageNotAnInteger
from django.db import IntegrityError
from django.http import Http404
from django.test import RequestFactory
from pyquery import PyQuery as pq
from waffle.models import Flag
from pytz import timezone, utc

from kuma.core.tests import eq_, ok_, KumaTestCase
from kuma.core.urlresolvers import reverse
from kuma.spam.akismet import Akismet
from kuma.spam.constants import SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL
from kuma.wiki.models import (Document, Revision, RevisionAkismetSubmission,
                              DocumentDeletionLog)
from kuma.wiki.tests import document as create_document


from . import SampleRevisionsMixin, SocialTestMixin, UserTestCase, email, user
from ..models import User, UserBan
from ..signup import SignupForm
from ..views import delete_document, revert_document


TESTUSER_PASSWORD = 'testpass'


class OldProfileTestCase(UserTestCase):
    localizing_client = True

    def test_old_profile_url_gone(self):
        response = self.client.get('/users/edit', follow=True)
        eq_(404, response.status_code)


@pytest.mark.bans
class BanTestCase(UserTestCase):
    localizing_client = True

    def test_ban_permission(self):
        """The ban permission controls access to the ban view."""
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username='testuser',
                          password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': admin.username})
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(str(settings.LOGIN_URL) in resp['Location'])
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})
        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

    def test_ban_view(self):
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

        resp = self.client.post(ban_url, data)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])

        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        ok_(bans.count())

    def test_ban_nonexistent_user(self):
        # Attempting to ban a non-existent user should 404
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        nonexistent_username = 'foo'
        data = {'reason': 'Banned by unit test.'}
        ban_url = reverse('users.ban_user',
                          kwargs={'username': nonexistent_username})

        resp = self.client.post(ban_url, data)
        eq_(404, resp.status_code)

        bans = UserBan.objects.filter(user__username=nonexistent_username,
                                      by=admin,
                                      reason='Banned by unit test.')
        eq_(bans.count(), 0)

    def test_ban_without_reason(self):
        # Attempting to ban without a reason should return the form
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')

        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

        # POST without data kwargs
        resp = self.client.post(ban_url)

        eq_(200, resp.status_code)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        eq_(bans.count(), 0)

        # POST with a blank reason
        data = {'reason': ''}
        resp = self.client.post(ban_url, data)

        eq_(200, resp.status_code)

        bans = UserBan.objects.filter(user=testuser,
                                      by=admin,
                                      reason='Banned by unit test.')
        eq_(bans.count(), 0)

    def test_bug_811751_banned_user(self):
        """A banned user should not be viewable"""
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.user_detail', args=(testuser.username,))

        # User viewable if not banned
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

        # Ban User
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)

        # User not viewable if banned
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # Admin can view banned user
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url, follow=True)
        self.assertNotEqual(response.status_code, 403)

    def test_get_ban_user_view(self):
        # For an unbanned user get the ban_user view
        testuser = self.user_model.objects.get(username='testuser')
        admin = self.user_model.objects.get(username='admin')

        self.client.login(username='admin', password='testpass')
        ban_url = reverse('users.ban_user',
                          kwargs={'username': testuser.username})

        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

        # For a banned user redirect to user detail page
        UserBan.objects.create(user=testuser, by=admin,
                               reason='Banned by unit test.',
                               is_active=True)
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(testuser.get_absolute_url() in resp['Location'])


@pytest.mark.bans
class BanAndCleanupTestCase(UserTestCase):
    localizing_client = True

    def test_ban_permission(self):
        """The ban permission controls access to the ban and cleanup view."""
        admin = self.user_model.objects.get(username='admin')
        testuser = self.user_model.objects.get(username='testuser')

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username='testuser',
                          password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'username': admin.username})
        resp = self.client.get(ban_url)
        eq_(302, resp.status_code)
        ok_(str(settings.LOGIN_URL) in resp['Location'])
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'username': testuser.username})
        resp = self.client.get(ban_url)
        eq_(200, resp.status_code)

    def test_ban_nonexistent_user(self):
        """GETs to ban_user_and_cleanup for nonexistent user return 404."""
        testuser = self.user_model.objects.get(username='testuser')

        # GET request
        self.client.login(username='admin',
                          password='testpass')
        ban_url = reverse('users.ban_user_and_cleanup',
                          kwargs={'username': testuser.username})
        testuser.delete()
        resp = self.client.get(ban_url)
        eq_(404, resp.status_code)


@pytest.mark.bans
class BanUserAndCleanupSummaryTestCase(SampleRevisionsMixin, UserTestCase):
    localizing_client = True

    def setUp(self):
        super(BanUserAndCleanupSummaryTestCase, self).setUp()

        self.ban_testuser_url = reverse('users.ban_user_and_cleanup_summary',
                                        kwargs={'username': self.testuser.username})
        self.ban_testuser2_url = reverse('users.ban_user_and_cleanup_summary',
                                         kwargs={'username': self.testuser2.username})
        self.client.login(username='admin', password='testpass')

    def enable_akismet_and_mock_requests(self, mock_requests):
        """Enable Akismet and mock calls to it. Return the mock object."""
        Flag.objects.create(name=SPAM_SUBMISSIONS_FLAG, everyone=True)
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(SPAM_URL, content=Akismet.submission_success)
        return mock_requests

    def test_delete_document(self):
        """
        A given document can be deleted, and will create a corresponding DocumentDeletionLog.
        """
        factory = RequestFactory()
        request = factory.get(self.ban_testuser_url)
        request.user = self.admin

        # Trying to delete a document that is None will fail without error.
        success = delete_document(request, None)
        self.assertFalse(success)

        # Calling on a real document deletes the document and creates the log object
        self.assertFalse(DocumentDeletionLog.objects.exists())
        success = delete_document(request, self.document)
        self.assertTrue(success)
        self.assertFalse(Document.objects.filter(id=self.document.id).exists())
        self.assertTrue(DocumentDeletionLog.objects.exists())

    def test_revert_document(self):
        factory = RequestFactory()
        request = factory.get(self.ban_testuser_url)
        request.user = self.admin

        # Create a spam revision on top of the original good rev.
        revisions_created = self.create_revisions(
            num=1,
            document=self.document,
            creator=self.testuser)
        revision_id = revisions_created[0].id

        # Reverting a non-existent rev raises a 404
        with self.assertRaises(Http404):
            revert_document(request, revision_id + 1)

        # Reverting an existing rev succeeds
        success = revert_document(request, revision_id)
        self.assertTrue(success)
        self.document.refresh_from_db(fields=['current_revision'])
        self.assertNotEqual(revision_id, self.document.current_revision.id)

        # If an IntegrityError is raised when we try to revert, it fails without error.
        revision_id = self.document.current_revision.id
        with mock.patch('kuma.wiki.models.datetime') as datetime_mock:
            # Just get any old thing inside the call to raise an IntegrityError
            datetime_mock.now.side_effect = IntegrityError()

            success = revert_document(request, revision_id)
        self.assertFalse(success)
        self.document.refresh_from_db(fields=['current_revision'])
        self.assertEqual(revision_id, self.document.current_revision.id)

    def test_ban_nonexistent_user(self):
        """POSTs to ban_user_and_cleanup for nonexistent user return 404."""
        self.testuser.delete()
        resp = self.client.post(self.ban_testuser_url)
        eq_(404, resp.status_code)

    def test_post_returns_summary_page(self):
        """POSTing to ban_user_and_cleanup returns the summary page."""
        resp = self.client.post(self.ban_testuser_url)
        eq_(200, resp.status_code)

    def test_post_bans_user(self):
        """POSTing to the ban_user_and_cleanup bans user for "spam" reason."""
        resp = self.client.post(self.ban_testuser_url)
        eq_(200, resp.status_code)

        testuser_banned = self.user_model.objects.get(username='testuser')
        ok_(not testuser_banned.is_active)

        bans = UserBan.objects.filter(user=self.testuser,
                                      by=self.admin,
                                      reason='Spam')
        ok_(bans.count())

    def test_post_banned_user(self):
        """POSTing to ban_user_and_cleanup for a banned user updates UserBan."""
        UserBan.objects.create(user=self.testuser, by=self.testuser2,
                               reason='Banned by unit test.',
                               is_active=True)

        resp = self.client.post(self.ban_testuser_url)
        eq_(200, resp.status_code)

        ok_(not self.testuser.is_active)

        bans = UserBan.objects.filter(user=self.testuser)

        # Assert that the ban exists, and 'by' and 'reason' fields are updated
        ok_(bans.count())
        eq_(bans.first().is_active, True)
        eq_(bans.first().by, self.admin)
        eq_(bans.first().reason, 'Spam')

    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    def test_post_submits_revisions_to_akismet_as_spam(self, mock_requests):
        """POSTing to ban_user_and_cleanup url submits revisions to akismet."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # Don't specify document so a new one is created for each revision
        num_revisions = 3
        revisions_created = self.create_revisions(
            num=num_revisions,
            creator=self.testuser)

        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # The request
        data = {'revision-id': [rev.id for rev in revisions_created]}
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # All of self.testuser's revisions have been submitted
        testuser_submissions = RevisionAkismetSubmission.objects.filter(revision__creator=self.testuser.id)
        eq_(testuser_submissions.count(), num_revisions)
        for submission in testuser_submissions:
            ok_(submission.revision in revisions_created)
        # Akismet endpoints were called twice for each revision
        ok_(mock_requests.called)
        eq_(mock_requests.call_count, 2 * num_revisions)

    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_when_no_user_revisions(self, mock_requests):
        """POSTing to ban_user_and_cleanup url for a user with no revisions."""
        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # User has no revisions
        data = {'revision-id': []}

        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # Akismet endpoints were not called
        eq_(mock_requests.call_count, 0)

    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_when_revisions_not_in_request(self, mock_requests):
        """POSTing to ban_user_and_cleanup url without revisions in request."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # Don't specify document so a new one is created for each revision
        num_revisions = 3
        self.create_revisions(
            num=num_revisions,
            creator=self.testuser)

        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # User's revisions were not in request.POST (not selected in the template)
        data = {'revision-id': []}

        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # No revisions submitted for self.testuser, since no revisions were selected
        testuser_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser.id)
        eq_(testuser_submissions.count(), 0)
        # Akismet endpoints were not called
        eq_(mock_requests.call_count, 0)

    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_when_wrong_revisions_in_request(self, mock_requests):
        """POSTing to ban_user_and_cleanup url with non-user revisions."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        num_revisions = 3
        revisions_created = self.create_revisions(
            num=num_revisions,
            document=self.document,
            creator=self.testuser)

        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # User being banned did not create the revisions being POSTed
        data = {'revision-id': [rev.id for rev in revisions_created]}

        resp = self.client.post(self.ban_testuser2_url, data=data)
        eq_(200, resp.status_code)

        # No revisions submitted for self.testuser2, since revisions in the POST
        # were made by self.testuser
        testuser2_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser2.id)
        eq_(testuser2_submissions.count(), 0)
        # Akismet endpoints were not called
        eq_(mock_requests.call_count, 0)

    def test_post_deletes_new_page(self):
        """POSTing to ban_user_and_cleanup url with a new document."""
        # Create a new document and revisions as testuser
        # Revisions will be reverted and then document will be deleted.
        new_document = create_document(save=True)
        new_revisions = self.create_revisions(
            num=3,
            document=new_document,
            creator=self.testuser)

        # Pass in all revisions, each should be reverted then the
        # document will be deleted as well
        data = {'revision-id': [rev.id for rev in new_revisions]}

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # Test that the document was deleted successfully
        deleted_doc = Document.admin_objects.filter(pk=new_document.pk).first()
        eq_(deleted_doc.deleted, True)

    def test_post_reverts_page(self):
        """POSTing to ban_user_and_cleanup url with revisions to a document."""
        # Create a new document and first revision as an admin
        # and spam revisions as testuser.
        # Document should be reverted with a new revision by admin.
        new_document = create_document(save=True)
        self.create_revisions(num=1, document=new_document, creator=self.admin)
        original_content = new_document.current_revision.content
        spam_revisions = self.create_revisions(
            num=3,
            document=new_document,
            creator=self.testuser)
        for rev in spam_revisions:
            rev.content = "Spam!"
            rev.save()

        # Before we send in the spam,
        # last spam_revisions[] should be the current revision
        eq_(new_document.current_revision.id, spam_revisions[2].id)
        # and testuser is the creator of this current revision
        eq_(new_document.current_revision.creator, self.testuser)

        # Pass in all spam revisions, each should be reverted then the
        # document should return to the original revision
        data = {'revision-id': [rev.id for rev in spam_revisions]}

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        new_document = Document.objects.filter(id=new_document.id).first()
        # Make sure that the current revision is not the spam revision
        for revision in spam_revisions:
            ok_(revision.id != new_document.current_revision.id)
        # The most recent Revision object should be the document's current revision
        latest_revision = Revision.objects.order_by('-id').first()
        eq_(new_document.current_revision.id, latest_revision.id)
        # Admin is the creator of this current revision
        eq_(new_document.current_revision.creator, self.admin)
        # The new revision's content is the same as the original's
        eq_(new_document.current_revision.content, original_content)

    def test_post_one_reverts_one_does_not_revert(self):
        """POSTing to ban_user_and_cleanup url with revisions to 2 documents."""
        # Document A will have latest revision by the admin, but older spam revisions
        # Document B will have latest revision by spammer
        # Document A should not revert (although there are older spam revisions)
        # Document B will revert
        new_document_a = create_document(save=True)
        new_document_b = create_document(save=True)
        self.create_revisions(
            num=1, document=new_document_a, creator=self.admin)
        self.create_revisions(
            num=1, document=new_document_b, creator=self.admin)
        spam_revisions_a = self.create_revisions(
            num=3,
            document=new_document_a,
            creator=self.testuser)
        safe_revision_a = self.create_revisions(
            num=1,
            document=new_document_a,
            creator=self.admin)
        spam_revisions_b = self.create_revisions(
            num=3,
            document=new_document_b,
            creator=self.testuser)

        # Pass in all spam revisions:
        # A revisions will not be reverted
        # B revisions will be reverted
        data = {'revision-id': [rev.id for rev in spam_revisions_a + spam_revisions_b]}

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # Document A: No changes should have been made
        new_document_a = Document.objects.filter(id=new_document_a.id).first()
        eq_(new_document_a.current_revision.id, safe_revision_a[0].id)
        revisions_a = Revision.objects.filter(document=new_document_a)
        eq_(revisions_a.count(), 5)  # Total of 5 revisions, no new revisions were made

        # Document B: Make sure that the current revision is not the spam revision
        new_document_b = Document.objects.filter(id=new_document_b.id).first()
        for revision in spam_revisions_b:
            ok_(revision.id != new_document_b.current_revision.id)
        # The most recent Revision for this document
        # should be the document's current revision
        latest_revision_b = Revision.objects.filter(
            document=new_document_b).order_by('-id').first()
        eq_(new_document_b.current_revision.id, latest_revision_b.id)
        # Admin is the creator of this current revision
        eq_(new_document_b.current_revision.creator, self.admin)
        revisions_b = Revision.objects.filter(document=new_document_b)
        # 5 total revisions on B = 1 initial + 3 spam revisions + 1 new reverted revision
        eq_(revisions_b.count(), 5)

    def test_current_rev_is_non_spam(self):
        new_document = create_document(save=True)
        self.create_revisions(
            num=1, document=new_document, creator=self.admin)
        spam_revisions = self.create_revisions(
            num=3,
            document=new_document,
            creator=self.testuser)
        safe_revision = self.create_revisions(
            num=1,
            document=new_document,
            creator=self.admin)

        # Pass in spam revisions:
        data = {'revision-id': [rev.id for rev in spam_revisions]}

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # No changes should have been made to the document
        new_document = Document.objects.get(id=new_document.id)
        eq_(new_document.current_revision.id, safe_revision[0].id)
        revisions = Revision.objects.filter(document=new_document)
        eq_(revisions.count(), 5)  # Total of 5 revisions, no new revisions were made

    def test_intermediate_non_spam_rev(self):
        new_document = create_document(save=True)
        # Create 4 revisions: one good, one spam, one good, then finally one spam
        self.create_revisions(
            num=1, document=new_document, creator=self.admin)
        spam_revision1 = self.create_revisions(
            num=1,
            document=new_document,
            creator=self.testuser)
        safe_revision = self.create_revisions(
            num=1,
            document=new_document,
            creator=self.admin)
        # Set the content of the last good revision, so we can compare afterwards
        safe_revision[0].content = "Safe"
        safe_revision[0].save()
        spam_revision2 = self.create_revisions(
            num=1,
            document=new_document,
            creator=self.testuser)

        # Pass in spam revisions:
        data = {'revision-id': [rev.id for rev in spam_revision1 + spam_revision2]}

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        # The document should be reverted to the last good revision
        new_document = Document.objects.get(id=new_document.id)

        # Make sure that the current revision is not either of the spam revisions
        for revision in spam_revision1 + spam_revision2:
            ok_(revision.id != new_document.current_revision.id)

        # And that it did actually revert
        ok_(new_document.current_revision.id != safe_revision[0].id)

        revisions = Revision.objects.filter(document=new_document)
        eq_(revisions.count(), 5)  # Total of 5 revisions, a new revision was made

        eq_(new_document.current_revision.content, "Safe")

    def test_post_sends_email(self):
        # Add an existing good document with a spam rev
        new_document1 = create_document(save=True)
        self.create_revisions(
            num=1, document=new_document1, creator=self.admin)
        spam_revision1 = self.create_revisions(
            num=1,
            document=new_document1,
            creator=self.testuser)

        # Add a new purely spam document
        new_document2 = create_document(save=True)
        spam_revision2 = self.create_revisions(
            num=1,
            document=new_document2,
            creator=self.testuser)

        # Add a spammed document where a user submits a good rev on top
        new_document3 = create_document(save=True)
        self.create_revisions(
            num=1, document=new_document3, creator=self.admin)
        spam_revision3 = self.create_revisions(
            num=1,
            document=new_document3,
            creator=self.testuser)
        self.create_revisions(
            num=1, document=new_document3, creator=self.admin)

        eq_(len(mail.outbox), 0)

        # Pass in spam revisions:
        data = {'revision-id':
                [rev.id for rev in spam_revision1 + spam_revision2 + spam_revision3]}

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(self.ban_testuser_url, data=data)
        eq_(200, resp.status_code)

        tz = timezone(settings.TIME_ZONE)

        eq_(len(mail.outbox), 1)
        eq_(
            mail.outbox[0].body,
            dedent(
                """
                * ACTIONS TAKEN *

                Banned:

                  Name: {user.username}
                  ID: {user.pk}
                  Joined at: {date_joined}
                  Profile link: https://example.com/en-US/profiles/{user.username}

                Submitted to Akismet as spam:

                  - {rev1.title} [https://example.com{rev1_url}]
                  - {rev2.title} [https://example.com{rev2_url}]
                  - {rev3.title} [https://example.com{rev3_url}]

                Deleted:

                  - {rev2.document.title} [https://example.com{rev2_doc_url}]

                Reverted:

                  - {rev1.title} [https://example.com{rev1_url}]

                * NEEDS FOLLOW UP *

                Revisions skipped due to newer non-spam revision:

                  - {rev3.title} [https://example.com{rev3_url}]

                * NO ACTION TAKEN *

                Latest revision is non-spam:

                  - {rev3.title} [https://example.com{rev3_url}]
                """.format(
                    user=self.testuser,
                    date_joined=tz.localize(self.testuser.date_joined).astimezone(utc),
                    rev1=spam_revision1[0],
                    rev2=spam_revision2[0],
                    rev3=spam_revision3[0],
                    rev1_url=spam_revision1[0].get_absolute_url(),
                    rev2_url=spam_revision2[0].get_absolute_url(),
                    rev3_url=spam_revision3[0].get_absolute_url(),
                    rev2_doc_url=spam_revision2[0].document.get_absolute_url()
                )
            )
        )


class UserViewsTest(UserTestCase):
    localizing_client = True

    def setUp(self):
        super(UserViewsTest, self).setUp()
        self.old_debug = settings.DEBUG
        settings.DEBUG = True
        self.client.logout()

    def tearDown(self):
        settings.DEBUG = self.old_debug

    def _get_current_form_field_values(self, doc):
        # Scrape out the existing significant form field values.
        fields = ('username', 'email', 'fullname', 'title', 'organization',
                  'location', 'irc_nickname', 'interests')
        form = dict()
        lookup_pattern = '#{prefix}edit *[name="{prefix}{field}"]'
        prefix = 'user-'
        for field in fields:
            lookup = lookup_pattern.format(prefix=prefix, field=field)
            form[prefix + field] = doc.find(lookup).val()
        form[prefix + 'country'] = 'us'
        form[prefix + 'format'] = 'html'
        return form

    def test_user_detail_view(self):
        """A user can be viewed"""
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.user_detail', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        eq_(testuser.username,
            doc.find('#user-head.vcard .nickname').text())
        eq_(testuser.fullname,
            doc.find('#user-head.vcard .fn').text())
        eq_(testuser.title,
            doc.find('#user-head.vcard .title').text())
        eq_(testuser.organization,
            doc.find('#user-head.vcard .org').text())
        eq_(testuser.location,
            doc.find('#user-head.vcard .loc').text())
        eq_('IRC: ' + testuser.irc_nickname,
            doc.find('#user-head.vcard .irc').text())

    def test_my_user_page(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_detail_page'))
        eq_(302, resp.status_code)
        ok_(reverse('users.user_detail', args=(u.username,)) in
            resp['Location'])

    def test_bug_698971(self):
        """A non-numeric page number should not cause an error"""
        testuser = self.user_model.objects.get(username='testuser')

        url = '%s?page=asdf' % reverse('users.user_detail',
                                       args=(testuser.username,))

        try:
            self.client.get(url, follow=True)
        except PageNotAnInteger:
            self.fail("Non-numeric page number should not cause an error")

    def test_user_edit(self):
        testuser = self.user_model.objects.get(username='testuser')
        url = reverse('users.user_detail', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(0, doc.find('#user-head .edit .button').length)

        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_detail', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        edit_button = doc.find('#user-head .user-buttons #edit-user')
        eq_(1, edit_button.length)

        url = edit_button.attr('href')
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        eq_(testuser.fullname,
            doc.find('#user-edit input[name="user-fullname"]').val())
        eq_(testuser.title,
            doc.find('#user-edit input[name="user-title"]').val())
        eq_(testuser.organization,
            doc.find('#user-edit input[name="user-organization"]').val())
        eq_(testuser.location,
            doc.find('#user-edit input[name="user-location"]').val())
        eq_(testuser.irc_nickname,
            doc.find('#user-edit input[name="user-irc_nickname"]').val())

        new_attrs = {
            'user-username': testuser.username,
            'user-email': 'testuser@test.com',
            'user-fullname': "Another Name",
            'user-title': "Another title",
            'user-organization': "Another org",
        }

        response = self.client.post(url, new_attrs, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('#user-head').length)
        eq_(new_attrs['user-fullname'],
            doc.find('#user-head .fn').text())
        eq_(new_attrs['user-title'],
            doc.find('#user-head .user-info .title').text())
        eq_(new_attrs['user-organization'],
            doc.find('#user-head .user-info .org').text())

        testuser = self.user_model.objects.get(username=testuser.username)
        eq_(new_attrs['user-fullname'], testuser.fullname)
        eq_(new_attrs['user-title'], testuser.title)
        eq_(new_attrs['user-organization'], testuser.organization)

    def test_my_user_edit(self):
        u = self.user_model.objects.get(username='testuser')
        self.client.login(username=u.username, password=TESTUSER_PASSWORD)
        resp = self.client.get(reverse('users.my_edit_page'))
        eq_(302, resp.status_code)
        ok_(reverse('users.user_edit', args=(u.username,)) in
            resp['Location'])

    def test_user_edit_beta(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_(None, doc.find('input#id_user-beta').attr('checked'))

        form = self._get_current_form_field_values(doc)
        form['user-beta'] = True

        self.client.post(url, form, follow=True)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        eq_('checked', doc.find('input#id_user-beta').attr('checked'))

    def test_user_edit_websites(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_sites = {
            'twitter': 'http://twitter.com/lmorchard',
            'stackoverflow': 'http://stackoverflow.com/users/lmorchard',
            'linkedin': 'https://www.linkedin.com/in/testuser',
            'mozillians': 'https://mozillians.org/u/testuser',
            'facebook': 'https://www.facebook.com/test.user'
        }

        form = self._get_current_form_field_values(doc)

        # Fill out the form with websites.
        form.update(dict(('user-%s_url' % k, v)
                         for k, v in test_sites.items()))

        # Submit the form, verify redirect to user detail
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#user-head').length)

        testuser = self.user_model.objects.get(pk=testuser.pk)

        # Verify the websites are saved in the user.
        for site, url in test_sites.items():
            url_attr_name = '%s_url' % site
            eq_(getattr(testuser, url_attr_name), url)

        # Verify the saved websites appear in the editing form
        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)
        for k, v in test_sites.items():
            eq_(v, doc.find('#user-edit *[name="user-%s_url"]' % k).val())

        # Github is not an editable field
        github_div = doc.find("#field_github_url div.field-account")
        github_acct = testuser.socialaccount_set.get()
        assert github_div.html().strip() == github_acct.get_profile_url()

        # Come up with some bad sites, either invalid URL or bad URL prefix
        bad_sites = {
            'linkedin': 'HAHAHA WHAT IS A WEBSITE',
            'twitter': 'http://facebook.com/lmorchard',
            'stackoverflow': 'http://overqueueblah.com/users/lmorchard',
        }
        form.update(dict(('user-%s_url' % k, v)
                         for k, v in bad_sites.items()))

        # Submit the form, verify errors for all of the bad sites
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#user-edit').length)
        tmpl = '#user-edit #users .%s .errorlist'
        for n in ('linkedin', 'twitter', 'stackoverflow'):
            eq_(1, doc.find(tmpl % n).length)

    def test_user_edit_interests(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_tags = ['javascript', 'css', 'canvas', 'html', 'homebrewing']

        form = self._get_current_form_field_values(doc)

        form['user-interests'] = ', '.join(test_tags)

        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)
        eq_(1, doc.find('#user-head').length)

        result_tags = [t.name.replace('profile:interest:', '')
                       for t in testuser.tags.all_ns('profile:interest:')]
        result_tags.sort()
        test_tags.sort()
        eq_(test_tags, result_tags)

        test_expertise = ['css', 'canvas']
        form['user-expertise'] = ', '.join(test_expertise)
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('#user-head').length)

        result_tags = [t.name.replace('profile:expertise:', '')
                       for t in testuser.tags.all_ns('profile:expertise')]
        result_tags.sort()
        test_expertise.sort()
        eq_(test_expertise, result_tags)

        # Now, try some expertise tags not covered in interests
        test_expertise = ['css', 'canvas', 'mobile', 'movies']
        form['user-expertise'] = ', '.join(test_expertise)
        response = self.client.post(url, form, follow=True)
        doc = pq(response.content)

        eq_(1, doc.find('.error #id_user-expertise').length)

    def test_bug_709938_interests(self):
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        doc = pq(response.content)

        test_tags = [u'science,Technology,paradox,knowledge,modeling,big data,'
                     u'vector,meme,heuristics,harmony,mathesis universalis,'
                     u'symmetry,mathematics,computer graphics,field,chemistry,'
                     u'religion,astronomy,physics,biology,literature,'
                     u'spirituality,Art,Philosophy,Psychology,Business,Music,'
                     u'Computer Science']

        form = self._get_current_form_field_values(doc)

        form['user-interests'] = test_tags

        response = self.client.post(url, form, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, doc.find('ul.errorlist li').length)
        assert ('Ensure this value has at most 255 characters'
                in doc.find('ul.errorlist li').text())

    def test_bug_698126_l10n(self):
        """Test that the form field names are localized"""
        testuser = self.user_model.objects.get(username='testuser')
        self.client.login(username=testuser.username,
                          password=TESTUSER_PASSWORD)

        url = reverse('users.user_edit', args=(testuser.username,))
        response = self.client.get(url, follow=True)
        for field in response.context['user_form'].fields:
            # if label is localized it's a lazy proxy object
            ok_(not isinstance(
                response.context['user_form'].fields[field].label, basestring),
                'Field %s is a string!' % field)


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


class KumaGitHubTests(UserTestCase, SocialTestMixin):
    localizing_client = False

    def setUp(self):
        self.signup_url = reverse('socialaccount_signup',
                                  locale=settings.WIKI_DEFAULT_LANGUAGE)

    def test_login(self):
        resp = self.github_login()
        self.assertRedirects(resp, self.signup_url)

    @override_config(RECAPTCHA_PRIVATE_KEY='private_key',
                     RECAPTCHA_PUBLIC_KEY='public_key')
    def test_signin_captcha(self):
        resp = self.github_login()
        self.assertRedirects(resp, self.signup_url)

        data = {'website': '',
                'username': 'octocat',
                'email': 'octo.cat@github-inc.com',
                'terms': True,
                'g-recaptcha-response': 'FAILED'}

        with mock.patch('captcha.client.request') as request_mock:
            request_mock.return_value.read.return_value = '{"success": null}'
            response = self.client.post(self.signup_url, data=data, follow=True)
        eq_(response.status_code, 200)
        eq_(response.context['form'].errors,
            {'captcha': [u'Incorrect, please try again.']})

    def test_matching_user(self):
        self.github_login()
        response = self.client.get(self.signup_url)
        self.assertTrue('matching_user' in response.context)
        self.assertEqual(response.context['matching_user'], None)
        octocat = user(username='octocat', save=True)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context['matching_user'], octocat)

    @mock.patch.dict(os.environ, {'RECAPTCHA_TESTING': 'True'})
    def test_email_addresses(self):
        public_email = 'octocat-public@example.com'
        private_email = 'octocat-private@example.com'
        unverified_email = 'octocat-trash@example.com'
        profile_data = self.github_profile_data.copy()
        profile_data['email'] = public_email
        email_data = [
            {
                'email': private_email,
                'verified': True,
                'primary': True
            }, {
                'email': unverified_email,
                'verified': False,
                'primary': False
            }
        ]
        self.github_login(profile_data=profile_data, email_data=email_data)
        response = self.client.get(self.signup_url)
        assert private_email not in response.context
        email_address = response.context['email_addresses']

        # first check if the public email address has been found
        self.assertTrue(public_email in email_address)
        self.assertEqual(email_address[public_email],
                         {'verified': False,
                          'email': public_email,
                          'primary': False})
        # then check if the private and verified-at-GitHub email address
        # has been found
        self.assertTrue(private_email in email_address)
        self.assertEqual(email_address[private_email],
                         {'verified': True,
                          'email': private_email,
                          'primary': True})
        # then check if the radio button's default value is the public email
        # address
        self.assertEqual(response.context['form'].initial['email'],
                         public_email)

        unverified_email = 'o.ctocat@gmail.com'
        data = {
            'website': '',
            'username': 'octocat',
            'email': SignupForm.other_email_value,  # = use other_email
            'other_email': unverified_email,
            'terms': True,
            'g-recaptcha-response': 'PASSED',
        }
        self.assertFalse((EmailAddress.objects.filter(email=unverified_email)
                                              .exists()))
        response = self.client.post(self.signup_url, data=data, follow=True)
        unverified_email_addresses = EmailAddress.objects.filter(
            email=unverified_email)
        self.assertTrue(unverified_email_addresses.exists())
        self.assertEquals(unverified_email_addresses.count(), 1)
        self.assertTrue(unverified_email_addresses[0].primary)
        self.assertFalse(unverified_email_addresses[0].verified)

    def test_email_addresses_with_no_public(self):
        profile_data = self.github_profile_data.copy()
        profile_data['email'] = None
        email_data = self.github_email_data[:]
        private_email = 'octocat.private@example.com'
        email_data[0]['email'] = private_email
        self.github_login(profile_data=profile_data, email_data=email_data)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context["form"].initial["email"],
                         private_email)

    def test_email_addresses_with_no_alternatives(self):
        private_email = self.github_profile_data['email']
        self.github_login(email_data=[])
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context["form"].initial["email"],
                         private_email)

    def test_no_email_addresses(self):
        """Note: this does not seem to currently happen."""
        profile_data = self.github_profile_data.copy()
        profile_data['email'] = None
        self.github_login(profile_data=profile_data, email_data=[])
        response = self.client.get(self.signup_url)
        self.assertEqual(response.context["form"].initial["email"], '')

    def test_matching_accounts(self):
        testemail = 'octo.cat.III@github-inc.com'
        profile_data = self.github_profile_data.copy()
        profile_data['email'] = testemail
        email_data = self.github_email_data[:]
        email_data[0]['email'] = testemail
        self.github_login(profile_data=profile_data, email_data=email_data)
        response = self.client.get(self.signup_url)
        self.assertFalse(response.context['matching_accounts'])

        # assuming there is already a Persona account with the given email
        # address
        octocat3 = user(username='octocat3', is_active=True,
                        email=testemail, password='test', save=True)
        social_account = SocialAccount.objects.create(uid=testemail,
                                                      provider='persona',
                                                      user=octocat3)
        response = self.client.get(self.signup_url)
        # TODO: what is new path here?
        self.assertEqual(list(response.context['matching_accounts']),
                         [social_account])

    def test_account_tokens(self):
        testemail = 'account_token@acme.com'
        testuser = user(username='user', is_active=True,
                        email=testemail, password='test', save=True)
        email(user=testuser, email=testemail,
              primary=True, verified=True, save=True)
        self.client.login(username=testuser.username, password='test')

        token = 'access_token'
        refresh_token = 'refresh_token'
        token_data = self.github_token_data.copy()
        token_data['access_token'] = token
        token_data['refresh_token'] = refresh_token

        self.github_login(token_data=token_data, process='connect')
        social_account = SocialAccount.objects.get(user=testuser,
                                                   provider='github')
        social_token = social_account.socialtoken_set.get()
        self.assertEqual(token, social_token.token)
        self.assertEqual(refresh_token, social_token.token_secret)

    def test_account_refresh_token_saved_next_login(self):
        """
        fails if a login missing a refresh token, deletes the previously
        saved refresh token. Systems such as google's oauth only send
        a refresh token on first login.
        """
        # Setup a user with a token and refresh token
        testemail = 'account_token@acme.com'
        testuser = user(username='user', is_active=True,
                        email=testemail, password='test', save=True)
        email(user=testuser, email=testemail,
              primary=True, verified=True, save=True)
        token = 'access_token'
        refresh_token = 'refresh_token'
        app = self.ensure_github_app()
        sa = testuser.socialaccount_set.create(provider=app.provider)
        sa.socialtoken_set.create(app=app, token=token, token_secret=refresh_token)

        # Login without a refresh token
        token_data = self.github_token_data.copy()
        token_data['access_token'] = token
        self.github_login(token_data=token_data, process='login')

        # Refresh token is still in database
        sa.refresh_from_db()
        social_token = sa.socialtoken_set.get()
        self.assertEqual(token, social_token.token)
        self.assertEqual(refresh_token, social_token.token_secret)


class UserDeleteTests(KumaTestCase):
    def test_missing_user_is_missing(self):
        assert not User.objects.filter(username='missing').exists()
        url = reverse('users.user_delete', kwargs={'username': 'missing'})
        response = self.client.get(url, follow=True)
        assert response.status_code == 404

    def test_wrong_user_is_forbidden(self):
        assert user(username='right', save=True)
        assert user(username='wrong', password='wrong', save=True)
        self.client.login(username='wrong', password='wrong')
        url = reverse('users.user_delete', kwargs={'username': 'right'})
        response = self.client.get(url, follow=True)
        assert response.status_code == 403

    def test_right_user_is_ok(self):
        assert user(username='user', password='password', save=True)
        self.client.login(username='user', password='password')
        url = reverse('users.user_delete', kwargs={'username': 'user'})
        response = self.client.get(url, follow=True)
        assert response.status_code == 200


class SendRecoveryEmailTests(KumaTestCase):
    def test_send_email(self):
        url = reverse('users.send_recovery_email', force_locale=True)
        response = self.client.post(url, {'email': 'test@example.com'},
                                    follow=True)
        next_url = reverse('users.recovery_email_sent', force_locale=True)
        self.assertRedirects(response, next_url)

    def test_bad_email(self):
        url = reverse('users.send_recovery_email', force_locale=True)
        response = self.client.post(url, {'email': 'not an email'})
        assert response.status_code == 400


class RecoverTests(KumaTestCase):

    def setUp(self):
        self.user = user(username='legacy', password='password', save=True)

    def test_recover_valid(self):
        recover_url = self.user.get_recovery_url()
        response = self.client.get(recover_url, follow=True)
        next_url = reverse('users.recover_done', force_locale=True)
        self.assertRedirects(response, next_url)
        self.user.refresh_from_db()
        assert not self.user.has_usable_password()

    def test_invalid_token_fails(self):
        recover_url = self.user.get_recovery_url()
        last_char = recover_url[-1]
        bad_last_char = '2' if last_char == '3' else '3'
        bad_recover_url = recover_url[:-1] + bad_last_char
        response = self.client.get(bad_recover_url)
        assert 'This link is no longer valid.' in response.content

    def test_invalid_uid_fails(self):
        assert not User.objects.filter(id=666).exists()
        self.user.id = 666
        bad_recover_url = self.user.get_recovery_url()
        response = self.client.get(bad_recover_url)
        assert 'This link is no longer valid.' in response.content
