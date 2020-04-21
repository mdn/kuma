from dataclasses import dataclass
from datetime import timedelta
from textwrap import dedent
from unittest import mock
from urllib.parse import urlencode

import pytest
import requests_mock
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from constance.test.utils import override_config
from django.conf import settings
from django.core import mail
from django.db import IntegrityError
from django.http import Http404
from django.test import RequestFactory
from pyquery import PyQuery as pq
from pytz import timezone, utc
from requests.exceptions import ProxyError, SSLError
from waffle.models import Flag

from kuma.attachments.models import Attachment, AttachmentRevision
from kuma.authkeys.models import Key
from kuma.core.ga_tracking import (
    ACTION_AUTH_STARTED,
    ACTION_AUTH_SUCCESSFUL,
    ACTION_FREE_NEWSLETTER,
    ACTION_PROFILE_AUDIT,
    ACTION_PROFILE_CREATED,
    ACTION_PROFILE_EDIT,
    ACTION_PROFILE_EDIT_ERROR,
    ACTION_RETURNING_USER_SIGNIN,
    CATEGORY_SIGNUP_FLOW,
)
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.core.utils import to_html
from kuma.spam.akismet import Akismet
from kuma.spam.constants import SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL
from kuma.wiki.models import (
    Document,
    DocumentDeletionLog,
    DocumentSpamAttempt,
    Revision,
    RevisionAkismetSubmission,
)
from kuma.wiki.templatetags.jinja_helpers import absolutify
from kuma.wiki.tests import document as create_document

from . import SampleRevisionsMixin, SocialTestMixin, user, UserTestCase
from ..models import User, UserBan, UserSubscription
from ..views import delete_document, revert_document


@dataclass
class StripeSubscription:
    id: str


def test_old_profile_url_gone(db, client):
    response = client.get("/users/edit", follow=True)
    assert response.status_code == 404


class BanTestCase(UserTestCase):
    def test_ban_permission(self):
        """The ban permission controls access to the ban view."""
        admin = self.user_model.objects.get(username="admin")
        testuser = self.user_model.objects.get(username="testuser")

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username="testuser", password="testpass")
        ban_url = reverse("users.ban_user", kwargs={"username": admin.username})
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)
        assert reverse(settings.LOGIN_URL) in resp["Location"]
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username="admin", password="testpass")
        ban_url = reverse("users.ban_user", kwargs={"username": testuser.username})
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

    def test_ban_view(self):
        testuser = self.user_model.objects.get(username="testuser")
        admin = self.user_model.objects.get(username="admin")

        self.client.login(username="admin", password="testpass")

        data = {"reason": "Banned by unit test."}
        ban_url = reverse("users.ban_user", kwargs={"username": testuser.username})

        resp = self.client.post(ban_url, data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)
        assert testuser.get_absolute_url() in resp["Location"]

        testuser_banned = self.user_model.objects.get(username="testuser")
        assert not testuser_banned.is_active

        bans = UserBan.objects.filter(
            user=testuser, by=admin, reason="Banned by unit test."
        )
        assert bans.count()

    def test_ban_nonexistent_user(self):
        # Attempting to ban a non-existent user should 404
        admin = self.user_model.objects.get(username="admin")

        self.client.login(username="admin", password="testpass")

        nonexistent_username = "foo"
        data = {"reason": "Banned by unit test."}
        ban_url = reverse("users.ban_user", kwargs={"username": nonexistent_username})

        resp = self.client.post(ban_url, data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 404
        assert_no_cache_header(resp)

        bans = UserBan.objects.filter(
            user__username=nonexistent_username, by=admin, reason="Banned by unit test."
        )
        assert bans.count() == 0

    def test_ban_without_reason(self):
        # Attempting to ban without a reason should return the form
        testuser = self.user_model.objects.get(username="testuser")
        admin = self.user_model.objects.get(username="admin")

        self.client.login(username="admin", password="testpass")

        ban_url = reverse("users.ban_user", kwargs={"username": testuser.username})

        # POST without data kwargs
        resp = self.client.post(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        bans = UserBan.objects.filter(
            user=testuser, by=admin, reason="Banned by unit test."
        )
        assert bans.count() == 0

        # POST with a blank reason
        data = {"reason": ""}
        resp = self.client.post(ban_url, data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        bans = UserBan.objects.filter(
            user=testuser, by=admin, reason="Banned by unit test."
        )
        assert bans.count() == 0

    def test_bug_811751_banned_user(self):
        """A banned user should not be viewable"""
        testuser = self.user_model.objects.get(username="testuser")
        url = reverse("users.user_detail", args=(testuser.username,))

        # User viewable if not banned
        response = self.client.get(url)
        assert response.status_code == 200
        assert_no_cache_header(response)

        # Ban User
        admin = self.user_model.objects.get(username="admin")
        testuser = self.user_model.objects.get(username="testuser")
        UserBan.objects.create(
            user=testuser, by=admin, reason="Banned by unit test.", is_active=True
        )

        # User not viewable if banned
        response = self.client.get(url)
        assert response.status_code == 404
        assert_no_cache_header(response)

        # Admin can view banned user
        self.client.login(username="admin", password="testpass")
        response = self.client.get(url)
        assert response.status_code == 200
        assert_no_cache_header(response)

    def test_get_ban_user_view(self):
        # For an unbanned user get the ban_user view
        testuser = self.user_model.objects.get(username="testuser")
        admin = self.user_model.objects.get(username="admin")

        self.client.login(username="admin", password="testpass")
        ban_url = reverse("users.ban_user", kwargs={"username": testuser.username})

        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # For a banned user redirect to user detail page
        UserBan.objects.create(
            user=testuser, by=admin, reason="Banned by unit test.", is_active=True
        )
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)
        assert testuser.get_absolute_url() in resp["Location"]


class BanAndCleanupTestCase(UserTestCase):
    def test_ban_permission(self):
        """The ban permission controls access to the ban and cleanup view."""
        admin = self.user_model.objects.get(username="admin")
        testuser = self.user_model.objects.get(username="testuser")

        # testuser doesn't have ban permission, can't ban.
        self.client.login(username="testuser", password="testpass")
        ban_url = reverse(
            "users.ban_user_and_cleanup", kwargs={"username": admin.username}
        )
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)
        assert reverse(settings.LOGIN_URL) in resp["Location"]
        self.client.logout()

        # admin has ban permission, can ban.
        self.client.login(username="admin", password="testpass")
        ban_url = reverse(
            "users.ban_user_and_cleanup", kwargs={"username": testuser.username}
        )
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

    def test_ban_nonexistent_user(self):
        """GETs to ban_user_and_cleanup for nonexistent user return 404."""
        testuser = self.user_model.objects.get(username="testuser")

        # GET request
        self.client.login(username="admin", password="testpass")
        ban_url = reverse(
            "users.ban_user_and_cleanup", kwargs={"username": testuser.username}
        )
        testuser.delete()
        resp = self.client.get(ban_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 404
        assert_no_cache_header(resp)


class BanUserAndCleanupSummaryTestCase(SampleRevisionsMixin, UserTestCase):
    def setUp(self):
        super(BanUserAndCleanupSummaryTestCase, self).setUp()

        self.ban_testuser_url = reverse(
            "users.ban_user_and_cleanup_summary",
            kwargs={"username": self.testuser.username},
        )
        self.ban_testuser2_url = reverse(
            "users.ban_user_and_cleanup_summary",
            kwargs={"username": self.testuser2.username},
        )
        self.client.login(username="admin", password="testpass")
        self.submissions_flag = None

    def tearDown(self):
        super(BanUserAndCleanupSummaryTestCase, self).tearDown()
        if self.submissions_flag:
            self.submissions_flag.delete()

    def enable_akismet_and_mock_requests(self, mock_requests):
        """Enable Akismet and mock calls to it. Return the mock object."""
        self.submissions_flag = Flag.objects.create(
            name=SPAM_SUBMISSIONS_FLAG, everyone=True
        )
        mock_requests.post(VERIFY_URL, content=b"valid")
        mock_requests.post(SPAM_URL, content=Akismet.submission_success.encode())
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
        assert not success

        # Calling on a real document deletes the document and creates the log object
        assert not DocumentDeletionLog.objects.exists()
        success = delete_document(request, self.document)
        assert success
        assert not Document.objects.filter(id=self.document.id).exists()
        assert DocumentDeletionLog.objects.exists()

    def test_revert_document(self):
        factory = RequestFactory()
        request = factory.get(self.ban_testuser_url)
        request.user = self.admin

        # Create a spam revision on top of the original good rev.
        revisions_created = self.create_revisions(
            num=1, document=self.document, creator=self.testuser
        )
        revision_id = revisions_created[0].id

        # Reverting a non-existent rev raises a 404
        with pytest.raises(Http404):
            revert_document(request, revision_id + 1)

        # Reverting an existing rev succeeds
        success = revert_document(request, revision_id)
        assert success
        self.document.refresh_from_db(fields=["current_revision"])
        assert self.document.current_revision.id != revision_id

        # If an IntegrityError is raised when we try to revert, it fails without error.
        revision_id = self.document.current_revision.id
        with mock.patch("kuma.wiki.models.datetime") as datetime_mock:
            # Just get any old thing inside the call to raise an IntegrityError
            datetime_mock.now.side_effect = IntegrityError()

            success = revert_document(request, revision_id)
        assert not success
        self.document.refresh_from_db(fields=["current_revision"])
        assert self.document.current_revision.id == revision_id

    def test_ban_nonexistent_user(self):
        """POSTs to ban_user_and_cleanup for nonexistent user return 404."""
        self.testuser.delete()
        resp = self.client.post(self.ban_testuser_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 404
        assert_no_cache_header(resp)

    def test_post_returns_summary_page(self):
        """POSTing to ban_user_and_cleanup returns the summary page."""
        resp = self.client.post(self.ban_testuser_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

    def test_post_bans_user(self):
        """POSTing to the ban_user_and_cleanup bans user for "spam" reason."""
        resp = self.client.post(self.ban_testuser_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        testuser_banned = self.user_model.objects.get(username="testuser")
        assert not testuser_banned.is_active

        bans = UserBan.objects.filter(user=self.testuser, by=self.admin, reason="Spam")
        assert bans.count()

    def test_post_banned_user(self):
        """POSTing to ban_user_and_cleanup for a banned user updates UserBan."""
        UserBan.objects.create(
            user=self.testuser,
            by=self.testuser2,
            reason="Banned by unit test.",
            is_active=True,
        )

        resp = self.client.post(self.ban_testuser_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        assert not self.testuser.is_active

        bans = UserBan.objects.filter(user=self.testuser)

        # Assert that the ban exists, and 'by' and 'reason' fields are updated
        assert bans.count()
        assert bans.first().is_active
        assert bans.first().by == self.admin
        assert bans.first().reason == "Spam"

    @override_config(AKISMET_KEY="dashboard")
    @requests_mock.mock()
    def test_post_submits_revisions_to_akismet_as_spam(self, mock_requests):
        """POSTing to ban_user_and_cleanup url submits revisions to akismet."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # Don't specify document so a new one is created for each revision
        num_revisions = 3
        revisions_created = self.create_revisions(
            num=num_revisions, creator=self.testuser
        )

        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # The request
        data = {"revision-id": [rev.id for rev in revisions_created]}
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # All of self.testuser's revisions have been submitted
        testuser_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser.id
        )
        assert testuser_submissions.count() == num_revisions
        for submission in testuser_submissions:
            assert submission.revision in revisions_created
        # Akismet endpoints were called twice for each revision
        assert mock_requests.called
        assert mock_requests.call_count == 2 * num_revisions

    @override_config(AKISMET_KEY="dashboard")
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_when_no_user_revisions(
        self, mock_requests
    ):
        """POSTing to ban_user_and_cleanup url for a user with no revisions."""
        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # User has no revisions
        data = {"revision-id": []}

        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # Akismet endpoints were not called
        assert mock_requests.call_count == 0

    @override_config(AKISMET_KEY="dashboard")
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_when_revisions_not_in_request(
        self, mock_requests
    ):
        """POSTing to ban_user_and_cleanup url without revisions in request."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        # Don't specify document so a new one is created for each revision
        num_revisions = 3
        self.create_revisions(num=num_revisions, creator=self.testuser)

        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # User's revisions were not in request.POST (not selected in the template)
        data = {"revision-id": []}

        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # No revisions submitted for self.testuser, since no revisions were selected
        testuser_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser.id
        )
        assert testuser_submissions.count() == 0
        # Akismet endpoints were not called
        assert mock_requests.call_count == 0

    @override_config(AKISMET_KEY="dashboard")
    @requests_mock.mock()
    def test_post_submits_no_revisions_to_akismet_when_wrong_revisions_in_request(
        self, mock_requests
    ):
        """POSTing to ban_user_and_cleanup url with non-user revisions."""
        # Create 3 revisions for self.testuser, titled 'Revision 1', 'Revision 2'...
        num_revisions = 3
        revisions_created = self.create_revisions(
            num=num_revisions, document=self.document, creator=self.testuser
        )

        # Enable Akismet and mock calls to it
        mock_requests = self.enable_akismet_and_mock_requests(mock_requests)

        # User being banned did not create the revisions being POSTed
        data = {"revision-id": [rev.id for rev in revisions_created]}

        resp = self.client.post(
            self.ban_testuser2_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # No revisions submitted for self.testuser2, since revisions in the POST
        # were made by self.testuser
        testuser2_submissions = RevisionAkismetSubmission.objects.filter(
            revision__creator=self.testuser2.id
        )
        assert testuser2_submissions.count() == 0
        # Akismet endpoints were not called
        assert mock_requests.call_count == 0

    def test_post_deletes_new_page(self):
        """POSTing to ban_user_and_cleanup url with a new document."""
        # Create a new document and revisions as testuser
        # Revisions will be reverted and then document will be deleted.
        new_document = create_document(save=True)
        new_revisions = self.create_revisions(
            num=3, document=new_document, creator=self.testuser
        )

        # Pass in all revisions, each should be reverted then the
        # document will be deleted as well
        data = {"revision-id": [rev.id for rev in new_revisions]}

        self.client.login(username="admin", password="testpass")
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # Test that the document was deleted successfully
        deleted_doc = Document.admin_objects.filter(pk=new_document.pk).first()
        assert deleted_doc.deleted

    def test_post_reverts_page(self):
        """POSTing to ban_user_and_cleanup url with revisions to a document."""
        # Create a new document and first revision as an admin
        # and spam revisions as testuser.
        # Document should be reverted with a new revision by admin.
        new_document = create_document(save=True)
        self.create_revisions(num=1, document=new_document, creator=self.admin)
        original_content = new_document.current_revision.content
        spam_revisions = self.create_revisions(
            num=3, document=new_document, creator=self.testuser
        )
        for rev in spam_revisions:
            rev.content = "Spam!"
            rev.save()

        # Before we send in the spam,
        # last spam_revisions[] should be the current revision
        assert new_document.current_revision.id == spam_revisions[2].id
        # and testuser is the creator of this current revision
        assert new_document.current_revision.creator == self.testuser

        # Pass in all spam revisions, each should be reverted then the
        # document should return to the original revision
        data = {"revision-id": [rev.id for rev in spam_revisions]}

        self.client.login(username="admin", password="testpass")
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        new_document = Document.objects.filter(id=new_document.id).first()
        # Make sure that the current revision is not the spam revision
        for revision in spam_revisions:
            assert revision.id != new_document.current_revision.id
        # The most recent Revision object should be the document's current revision
        latest_revision = Revision.objects.order_by("-id").first()
        assert new_document.current_revision.id == latest_revision.id
        # Admin is the creator of this current revision
        assert new_document.current_revision.creator == self.admin
        # The new revision's content is the same as the original's
        assert new_document.current_revision.content == original_content

    def test_post_one_reverts_one_does_not_revert(self):
        """POSTing to ban_user_and_cleanup url with revisions to 2 documents."""
        # Document A will have latest revision by the admin, but older spam revisions
        # Document B will have latest revision by spammer
        # Document A should not revert (although there are older spam revisions)
        # Document B will revert
        new_document_a = create_document(save=True)
        new_document_b = create_document(save=True)
        self.create_revisions(num=1, document=new_document_a, creator=self.admin)
        self.create_revisions(num=1, document=new_document_b, creator=self.admin)
        spam_revisions_a = self.create_revisions(
            num=3, document=new_document_a, creator=self.testuser
        )
        safe_revision_a = self.create_revisions(
            num=1, document=new_document_a, creator=self.admin
        )
        spam_revisions_b = self.create_revisions(
            num=3, document=new_document_b, creator=self.testuser
        )

        # Pass in all spam revisions:
        # A revisions will not be reverted
        # B revisions will be reverted
        data = {"revision-id": [rev.id for rev in spam_revisions_a + spam_revisions_b]}

        self.client.login(username="admin", password="testpass")
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # Document A: No changes should have been made
        new_document_a = Document.objects.filter(id=new_document_a.id).first()
        assert new_document_a.current_revision.id == safe_revision_a[0].id
        revisions_a = Revision.objects.filter(document=new_document_a)
        assert (
            revisions_a.count() == 5
        )  # Total of 5 revisions, no new revisions were made

        # Document B: Make sure that the current revision is not the spam revision
        new_document_b = Document.objects.filter(id=new_document_b.id).first()
        for revision in spam_revisions_b:
            assert revision.id != new_document_b.current_revision.id
        # The most recent Revision for this document
        # should be the document's current revision
        latest_revision_b = (
            Revision.objects.filter(document=new_document_b).order_by("-id").first()
        )
        assert new_document_b.current_revision.id == latest_revision_b.id
        # Admin is the creator of this current revision
        assert new_document_b.current_revision.creator == self.admin
        revisions_b = Revision.objects.filter(document=new_document_b)
        # 5 total revisions on B = 1 initial + 3 spam revisions + 1 new reverted revision
        assert revisions_b.count() == 5

    def test_current_rev_is_non_spam(self):
        new_document = create_document(save=True)
        self.create_revisions(num=1, document=new_document, creator=self.admin)
        spam_revisions = self.create_revisions(
            num=3, document=new_document, creator=self.testuser
        )
        safe_revision = self.create_revisions(
            num=1, document=new_document, creator=self.admin
        )

        # Pass in spam revisions:
        data = {"revision-id": [rev.id for rev in spam_revisions]}

        self.client.login(username="admin", password="testpass")
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # No changes should have been made to the document
        new_document = Document.objects.get(id=new_document.id)
        assert new_document.current_revision.id == safe_revision[0].id
        revisions = Revision.objects.filter(document=new_document)
        assert (
            revisions.count() == 5
        )  # Total of 5 revisions, no new revisions were made

    def test_intermediate_non_spam_rev(self):
        new_document = create_document(save=True)
        # Create 4 revisions: one good, one spam, one good, then finally one spam
        self.create_revisions(num=1, document=new_document, creator=self.admin)
        spam_revision1 = self.create_revisions(
            num=1, document=new_document, creator=self.testuser
        )
        safe_revision = self.create_revisions(
            num=1, document=new_document, creator=self.admin
        )
        # Set the content of the last good revision, so we can compare afterwards
        safe_revision[0].content = "Safe"
        safe_revision[0].save()
        spam_revision2 = self.create_revisions(
            num=1, document=new_document, creator=self.testuser
        )

        # Pass in spam revisions:
        data = {"revision-id": [rev.id for rev in spam_revision1 + spam_revision2]}

        self.client.login(username="admin", password="testpass")
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        # The document should be reverted to the last good revision
        new_document = Document.objects.get(id=new_document.id)

        # Make sure that the current revision is not either of the spam revisions
        for revision in spam_revision1 + spam_revision2:
            assert revision.id != new_document.current_revision.id

        # And that it did actually revert
        assert new_document.current_revision.id != safe_revision[0].id

        revisions = Revision.objects.filter(document=new_document)
        assert revisions.count() == 5  # Total of 5 revisions, a new revision was made
        assert new_document.current_revision.content == "Safe"

    def test_post_sends_email(self):
        # Add an existing good document with a spam rev
        new_document1 = create_document(save=True)
        self.create_revisions(num=1, document=new_document1, creator=self.admin)
        spam_revision1 = self.create_revisions(
            num=1, document=new_document1, creator=self.testuser
        )

        # Add a new purely spam document
        new_document2 = create_document(save=True)
        spam_revision2 = self.create_revisions(
            num=1, document=new_document2, creator=self.testuser
        )

        # Add a spammed document where a user submits a good rev on top
        new_document3 = create_document(save=True)
        self.create_revisions(num=1, document=new_document3, creator=self.admin)
        spam_revision3 = self.create_revisions(
            num=1, document=new_document3, creator=self.testuser
        )
        self.create_revisions(num=1, document=new_document3, creator=self.admin)

        assert len(mail.outbox) == 0

        # Pass in spam revisions:
        data = {
            "revision-id": [
                rev.id for rev in spam_revision1 + spam_revision2 + spam_revision3
            ]
        }

        self.client.login(username="admin", password="testpass")
        resp = self.client.post(
            self.ban_testuser_url, data=data, HTTP_HOST=settings.WIKI_HOST
        )
        assert resp.status_code == 200
        assert_no_cache_header(resp)

        tz = timezone(settings.TIME_ZONE)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].body == dedent(
            """
            * ACTIONS TAKEN *

            Banned:

              Name: {user.username}
              ID: {user.pk}
              Joined at: {date_joined}
              Profile link: {user_url}

            Submitted to Akismet as spam:

              - {rev1.title} [{rev1_url}]
              - {rev2.title} [{rev2_url}]
              - {rev3.title} [{rev3_url}]

            Deleted:

              - {rev2.document.title} [{rev2_doc_url}]

            Reverted:

              - {rev1.title} [{rev1_url}]

            * NEEDS FOLLOW UP *

            Revisions skipped due to newer non-spam revision:

              - {rev3.title} [{rev3_url}]

            * NO ACTION TAKEN *

            Latest revision is non-spam:

              - {rev3.title} [{rev3_url}]
            """.format(
                user=self.testuser,
                user_url=absolutify(self.testuser.get_absolute_url()),
                date_joined=tz.localize(self.testuser.date_joined).astimezone(utc),
                rev1=spam_revision1[0],
                rev2=spam_revision2[0],
                rev3=spam_revision3[0],
                rev1_url=absolutify(spam_revision1[0].get_absolute_url()),
                rev2_url=absolutify(spam_revision2[0].get_absolute_url()),
                rev3_url=absolutify(spam_revision3[0].get_absolute_url()),
                rev2_doc_url=spam_revision2[0].document.get_full_url(),
            )
        )


def _get_current_form_field_values(doc):
    # Scrape out the existing significant form field values.
    fields = (
        "username",
        "fullname",
        "title",
        "organization",
        "location",
        "irc_nickname",
        "is_github_url_public",
    )
    form = dict()
    lookup_pattern = '#{prefix}edit *[name="{prefix}{field}"]'
    prefix = "user-"
    for field in fields:
        lookup = lookup_pattern.format(prefix=prefix, field=field)
        elements = doc.find(lookup)
        assert len(elements) == 1, "field = {}".format(field)
        element = elements[0]
        if element.type == "text":
            form[prefix + field] = element.value
        else:
            assert element.type == "checkbox"
            form[prefix + field] = element.checked

    form[prefix + "country"] = "us"
    form[prefix + "format"] = "html"
    return form


def test_user_detail_view(wiki_user, client):
    """A user can be viewed."""
    wiki_user.irc_nickname = "wooki"
    wiki_user.save()
    url = reverse("users.user_detail", args=(wiki_user.username,))
    response = client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    doc = pq(response.content)
    assert doc.find("#user-head.vcard .nickname").text() == wiki_user.username
    assert doc.find("#user-head.vcard .fn").text() == wiki_user.fullname
    assert doc.find("#user-head.vcard .title").text() == wiki_user.title
    assert doc.find("#user-head.vcard .org").text() == wiki_user.organization
    assert doc.find("#user-head.vcard .loc").text() == wiki_user.location
    assert doc.find("#user-head.vcard .irc").text() == (
        "IRC: " + wiki_user.irc_nickname
    )


def test_my_user_page(wiki_user, user_client):
    resp = user_client.get(reverse("users.my_detail_page"))
    assert resp.status_code == 302
    assert_no_cache_header(resp)
    assert resp["Location"].endswith(
        reverse("users.user_detail", args=(wiki_user.username,))
    )


def test_bug_698971(wiki_user, client):
    """A non-numeric page number should not raise an error."""
    url = reverse("users.user_detail", args=(wiki_user.username,))

    response = client.get(url, dict(page="asdf"))
    assert response.status_code == 200
    assert_no_cache_header(response)


def test_user_edit(wiki_user, client, user_client):
    url = reverse("users.user_detail", args=(wiki_user.username,))
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert_no_cache_header(response)
    doc = pq(response.content)
    assert doc.find("#user-head .edit .button").length == 0

    url = reverse("users.user_detail", args=(wiki_user.username,))
    response = user_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    doc = pq(response.content)
    edit_button = doc.find("#user-head .user-buttons #edit-user")
    assert edit_button.length == 1

    url = edit_button.attr("href")
    response = user_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    doc = pq(response.content)

    assert (
        doc.find('#user-edit input[name="user-fullname"]').val() == wiki_user.fullname
    )
    assert doc.find('#user-edit input[name="user-title"]').val() == wiki_user.title
    assert (
        doc.find('#user-edit input[name="user-organization"]').val()
        == wiki_user.organization
    )
    assert (
        doc.find('#user-edit input[name="user-location"]').val() == wiki_user.location
    )
    assert (
        doc.find('#user-edit input[name="user-irc_nickname"]').val()
        == wiki_user.irc_nickname
    )

    new_attrs = {
        "user-username": wiki_user.username,
        "user-fullname": "Another Name",
        "user-title": "Another title",
        "user-organization": "Another org",
    }

    response = user_client.post(url, new_attrs, follow=True)
    doc = pq(response.content)

    assert doc.find("#user-head").length == 1
    assert doc.find("#user-head .fn").text() == new_attrs["user-fullname"]
    assert doc.find("#user-head .user-info .title").text() == new_attrs["user-title"]
    assert (
        doc.find("#user-head .user-info .org").text() == new_attrs["user-organization"]
    )

    wiki_user.refresh_from_db()

    assert wiki_user.fullname == new_attrs["user-fullname"]
    assert wiki_user.title == new_attrs["user-title"]
    assert wiki_user.organization == new_attrs["user-organization"]


def test_my_user_edit(wiki_user, user_client):
    response = user_client.get(reverse("users.my_edit_page"))
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response["Location"].endswith(
        reverse("users.user_edit", args=(wiki_user.username,))
    )


def test_user_edit_beta(
    wiki_user, wiki_user_github_account, beta_testers_group, user_client
):
    url = reverse("users.user_edit", args=(wiki_user.username,))
    response = user_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    doc = pq(response.content)
    assert doc.find("input#id_user-beta").attr("checked") is None

    form = _get_current_form_field_values(doc)
    form["user-beta"] = True

    # Filter out keys with `None` values
    form = {k: v for k, v in form.items() if v is not None}

    response = user_client.post(url, form)
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response["Location"].endswith(
        reverse("users.user_detail", args=(wiki_user.username,))
    )

    response = user_client.get(url)
    assert response.status_code == 200
    doc = pq(response.content)
    assert doc.find("input#id_user-beta").attr("checked") == "checked"


def test_user_edit_websites(wiki_user, wiki_user_github_account, user_client):
    url = reverse("users.user_edit", args=(wiki_user.username,))
    response = user_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    doc = pq(response.content)

    test_sites = {
        "twitter": "http://twitter.com/lmorchard",
        "stackoverflow": "http://stackoverflow.com/users/lmorchard",
        "linkedin": "https://www.linkedin.com/in/testuser",
        "mozillians": "https://mozillians.org/u/testuser",
        "facebook": "https://www.facebook.com/test.user",
    }

    form = _get_current_form_field_values(doc)

    # Fill out the form with websites.
    form.update(dict(("user-%s_url" % k, v) for k, v in test_sites.items()))

    # Filter out keys with `None` values
    form = {k: v for k, v in form.items() if v is not None}

    # Submit the form, verify redirect to user detail
    response = user_client.post(url, form, follow=True)
    assert response.status_code == 200
    doc = pq(response.content)
    assert doc.find("#user-head").length == 1

    wiki_user.refresh_from_db()

    # Verify the websites are saved in the user.
    for site, site_url in test_sites.items():
        url_attr_name = "%s_url" % site
        assert getattr(wiki_user, url_attr_name) == site_url

    # Verify the saved websites appear in the editing form
    response = user_client.get(url)
    assert response.status_code == 200
    doc = pq(response.content)
    for k, v in test_sites.items():
        assert doc.find('#user-edit *[name="user-%s_url"]' % k).val() == v

    # Github is not an editable field
    github_div = doc.find("#field_github_url div.field-account")
    github_acct = wiki_user.socialaccount_set.get()
    assert to_html(github_div).strip() == github_acct.get_profile_url()

    # Come up with some bad sites, either invalid URL or bad URL prefix
    bad_sites = {
        "linkedin": "HAHAHA WHAT IS A WEBSITE",
        "twitter": "http://facebook.com/lmorchard",
        "stackoverflow": "http://overqueueblah.com/users/lmorchard",
    }
    form.update(dict(("user-%s_url" % k, v) for k, v in bad_sites.items()))

    # Submit the form, verify errors for all of the bad sites
    response = user_client.post(url, form, follow=True)
    doc = pq(response.content)
    assert doc.find("#user-edit").length == 1
    tmpl = "#user-edit #users .%s .errorlist"
    for n in ("linkedin", "twitter", "stackoverflow"):
        assert doc.find(tmpl % n).length == 1


def test_bug_698126_l10n(wiki_user, user_client):
    """Test that the form field names are localized"""
    url = reverse("users.user_edit", args=(wiki_user.username,))
    response = user_client.get(url, follow=True)
    for field in response.context["user_form"].fields:
        # if label is localized it's a lazy proxy object
        lbl = response.context["user_form"].fields[field].label
        assert not isinstance(lbl, str), "Field %s is a string!" % field


def test_user_edit_github_is_public(wiki_user, wiki_user_github_account, user_client):
    """A user can set that they want their GitHub to be public."""
    assert not wiki_user.is_github_url_public
    url = reverse("users.user_edit", args=(wiki_user.username,))
    response = user_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    form = _get_current_form_field_values(pq(response.content))
    assert not form["user-is_github_url_public"]
    form["user-is_github_url_public"] = True
    # Filter out keys with `None` values
    form = {k: v for k, v in form.items() if v is not None}
    response = user_client.post(url, form)
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response["Location"].endswith(
        reverse("users.user_detail", args=(wiki_user.username,))
    )
    wiki_user.refresh_from_db()
    assert wiki_user.is_github_url_public


@pytest.mark.parametrize("case", ("DOMAIN", "WIKI_HOST"))
def test_404_logins(db, client, case):
    """A login link should display within the body on the wiki 404 page."""
    response = client.get(
        "/something-doesnt-exist", follow=True, HTTP_HOST=getattr(settings, case)
    )
    assert response.status_code == 404
    signin_url = reverse("socialaccount_signin")
    signin_shown = pq(response.content).find(f'#content a[href^="{signin_url}"]')
    if case == "WIKI_HOST":
        assert signin_shown
    else:
        assert not signin_shown


@pytest.mark.parametrize("case", ("DOMAIN", "WIKI_HOST"))
def test_404_already_logged_in(user_client, case):
    """
    The login buttons should not display on the 404 page when the
    user is logged-in.
    """
    # View page as a logged in user
    response = user_client.get(
        "/something-doesnt-exist", follow=True, HTTP_HOST=getattr(settings, case)
    )
    assert response.status_code == 404
    assert not pq(response.content).find(".socialaccount-providers")


class KumaGitHubTests(UserTestCase, SocialTestMixin):
    def setUp(self):
        self.signup_url = reverse("socialaccount_signup")

    def test_login(self):
        resp = self.github_login()
        self.assertRedirects(resp, self.signup_url)

    def test_login_500_on_token(self):
        resp = self.github_login(token_status_code=500)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_500_on_getting_profile(self):
        resp = self.github_login(profile_status_code=500)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_500_on_getting_email_addresses(self):
        resp = self.github_login(email_status_code=500)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_SSLError_on_getting_profile(self):
        resp = self.github_login(profile_exc=SSLError)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_login_ProxyError_on_getting_email_addresses(self):
        resp = self.github_login(email_exc=ProxyError)
        # No redirect!
        assert resp.status_code == 200
        doc = pq(resp.content)
        assert "Account Sign In Failure" in doc.find("h1").text()

    def test_email_addresses(self):
        public_email = "octocat-public@example.com"
        private_email = "octocat-private@example.com"
        unverified_email = "octocat-trash@example.com"
        invalid_email = "xss><svg/onload=alert(document.cookie)>@example.com"
        profile_data = self.github_profile_data.copy()
        profile_data["email"] = public_email
        email_data = [
            # It might be unrealistic but let's make sure the primary email
            # is NOT first in the list. Just to prove that pick that email not
            # on it coming first but that's the primary verified one.
            {"email": unverified_email, "verified": False, "primary": False},
            {"email": private_email, "verified": True, "primary": True},
            {"email": invalid_email, "verified": False, "primary": False},
        ]
        self.github_login(profile_data=profile_data, email_data=email_data)
        response = self.client.get(self.signup_url)
        assert response.status_code == 200
        assert_no_cache_header(response)
        doc = pq(response.content)

        # The hidden input should display the primary verified email
        assert doc.find('input[name="email"]').val() == email_data[1]["email"]
        # But whatever's in the hidden email input is always displayed to the user
        # as "plain text". Check that that also is right.
        assert doc.find("#email-static-container").text() == email_data[1]["email"]

        unverified_email = "o.ctocat@gmail.com"
        data = {
            "website": "",
            "username": "octocat",
            "email": email_data[1]["email"],
            "terms": True,
        }
        assert not EmailAddress.objects.filter(email=unverified_email).exists()
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        # Check that the user.email field became the primary verified one.
        user = User.objects.get(username=data["username"])
        assert user.email == email_data[1]["email"]
        assert user.emailaddress_set.count() == 1
        assert user.emailaddress_set.first().email == user.email
        assert user.emailaddress_set.first().verified
        assert user.emailaddress_set.first().primary

    def test_signup_public_github(self, is_public=True):
        resp = self.github_login()
        assert resp.redirect_chain[-1][0].endswith(self.signup_url)

        data = {
            "website": "",
            "username": "octocat",
            "email": "octocat-private@example.com",
            "terms": True,
            "is_github_url_public": is_public,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)
        user = User.objects.get(username="octocat")
        assert user.is_github_url_public == is_public

    def test_signup_private_github(self):
        self.test_signup_public_github(is_public=False)

    def test_signup_github_event_tracking(self):
        """Tests that kuma.core.ga_tracking.track_event is called when you
        sign up with GitHub for the first time."""
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.views.track_event")
            p3 = mock.patch("kuma.users.providers.github.views.track_event")
            with p1 as track_event_mock_signals, p2 as track_event_mock_views, p3 as track_event_mock_github:

                self.github_login(
                    headers={
                        # Needed to trigger the 'auth-started' GA tracking event.
                        "HTTP_REFERER": "http://testserver/en-US/"
                    }
                )

                data = {
                    "website": "",
                    "username": "octocat",
                    "email": "octocat-private@example.com",
                    "terms": True,
                    "is_github_url_public": True,
                }
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 302
                assert User.objects.get(username="octocat")

                track_event_mock_signals.assert_has_calls(
                    [
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, "github"
                        ),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_CREATED, "github"
                        ),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_FREE_NEWSLETTER, "opt-out"
                        ),
                    ]
                )
                track_event_mock_github.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "github"
                )

                track_event_mock_views.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "github"
                )

    def test_signup_github_email_manual_override(self):
        """Tests if a POST request comes in with an email that is NOT one of the
        options, it should reject it.
        Basically, in the sign up, you are shown what you primary default is and
        it's also in a hidden input.
        So, the only want to try to sign up with anything outside of that would
        be if you manually control the POST request or fiddle with the DOM to
        edit the hidden email input.
        """
        self.github_login()
        data = {
            "website": "",
            "username": "octocat",
            "email": "wasnot@anoption.biz",
            "terms": True,
            "is_github_url_public": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 400

    def test_signup_username_edit_event_tracking(self):
        """
        Tests that GA tracking events are sent for editing the default suggested
        username when signing-up with a new account.
        """
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.views.track_event")
            p3 = mock.patch("kuma.users.providers.google.views.track_event")
            with p1, p2 as track_event_mock_views, p3:

                response = self.google_login()

                doc = pq(response.content)
                # Just sanity check what's the defaults in the form.
                # Remember, the self.google_login relies on the provider giving an
                # email that is 'example@gmail.com'
                assert doc.find('input[name="username"]').val() == "example"
                assert doc.find('input[name="email"]').val() == "example@gmail.com"

                data = {
                    "website": "",
                    "username": "better",
                    "email": "example@gmail.com",
                    "terms": False,  # Note!
                    "is_newsletter_subscribed": True,
                }
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 200

                track_event_mock_views.assert_has_calls(
                    [
                        mock.call(CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "google"),
                        # Note the lack of 'ACTION_PROFILE_EDIT' because the form
                        # submission was invalid and the save didn't go ahead.
                    ]
                )

                # This time, the form submission will work.
                data["terms"] = True
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 302

                # Sanity check that the right user got created
                assert User.objects.get(username="better")

                track_event_mock_views.assert_has_calls(
                    [
                        mock.call(CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "google"),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_EDIT, "username edit"
                        ),
                    ]
                )

    def test_signin_github_event_tracking(self):
        """Tests that kuma.core.ga_tracking.track_event is called when you
        sign in with GitHub a consecutive time."""
        # First sign up.
        self.github_login()
        data = {
            "website": "",
            "username": "octocat",
            "email": "octocat-private@example.com",
            "terms": True,
            "is_github_url_public": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        user = User.objects.get(username="octocat")

        # Pretend that some time goes by
        user.date_joined -= timedelta(minutes=1)
        user.save()

        # Now, this time sign in.
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            # This syntax looks a bit weird but it's just to avoid having
            # to write all mock patches on one super long line in the
            # 'with' statement.
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.providers.github.views.track_event")
            with p1 as track_event_mock_signals, p2 as track_event_mock_github:
                response = self.github_login(
                    follow=False,
                    # Needed to trigger the 'auth-started' GA tracking event.
                    headers={"HTTP_REFERER": "http://testserver/en-US/"},
                )
                assert response.status_code == 302

                track_event_mock_signals.assert_has_calls(
                    [
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, "github"
                        ),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_RETURNING_USER_SIGNIN, "github"
                        ),
                    ]
                )
                track_event_mock_github.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "github"
                )

    def test_account_tokens(self):
        testemail = "account_token@acme.com"
        testuser = user(
            username="user", is_active=True, email=testemail, password="test", save=True
        )
        EmailAddress.objects.create(
            user=testuser, email=testemail, primary=True, verified=True
        )
        self.client.login(username=testuser.username, password="test")

        token = "access_token"
        refresh_token = "refresh_token"
        token_data = self.github_token_data.copy()
        token_data["access_token"] = token
        token_data["refresh_token"] = refresh_token

        self.github_login(token_data=token_data, process="connect")
        social_account = SocialAccount.objects.get(user=testuser, provider="github")
        social_token = social_account.socialtoken_set.get()
        assert token == social_token.token
        assert refresh_token == social_token.token_secret

    def test_account_refresh_token_saved_next_login(self):
        """
        fails if a login missing a refresh token, deletes the previously
        saved refresh token. Systems such as google's oauth only send
        a refresh token on first login.
        """
        # Setup a user with a token and refresh token
        testemail = "account_token@acme.com"
        testuser = user(
            username="user", is_active=True, email=testemail, password="test", save=True
        )
        EmailAddress.objects.create(
            user=testuser, email=testemail, primary=True, verified=True
        )
        token = "access_token"
        refresh_token = "refresh_token"
        app = self.ensure_github_app()
        sa = testuser.socialaccount_set.create(provider=app.provider)
        sa.socialtoken_set.create(app=app, token=token, token_secret=refresh_token)

        # Login without a refresh token
        token_data = self.github_token_data.copy()
        token_data["access_token"] = token
        self.github_login(token_data=token_data, process="login")

        # Refresh token is still in database
        sa.refresh_from_db()
        social_token = sa.socialtoken_set.get()
        assert token == social_token.token
        assert refresh_token == social_token.token_secret


class KumaGoogleTests(UserTestCase, SocialTestMixin):
    def setUp(self):
        self.signup_url = reverse("socialaccount_signup")

    def test_signup_google(self):
        response = self.google_login()
        assert response.status_code == 200

        doc = pq(response.content)
        # The default suggested username should be the `email.split('@')[0]`
        email = self.google_profile_data["email"]
        username = email.split("@")[0]
        assert doc.find('input[name="username"]').val() == username
        # first remove the button from that container
        doc("#username-static-container button").remove()
        # so that what's left is just the username
        assert doc.find("#username-static-container").text() == username

        # The hidden input should display the primary verified email
        assert doc.find('input[name="email"]').val() == email
        # But whatever's in the hidden email input is always displayed to the user
        # as "plain text". Check that that also is right.
        assert doc.find("#email-static-container").text() == email

        data = {
            "website": "",  # for the honeypot
            "username": username,
            "email": email,
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 302
        assert_no_cache_header(response)

        user = User.objects.get(username=username)
        assert user.email == email

        assert EmailAddress.objects.filter(
            email=email, primary=True, verified=True
        ).exists()

    def test_signup_google_changed_email(self):
        """When you load the signup form, our backend recognizes what your valid
        email address can be. But what if someone changes the hidden input to
        something other that what's there by default. That should get kicked out.
        """
        self.google_login()
        email = self.google_profile_data["email"]
        username = email.split("@")[0]

        data = {
            "website": "",  # for the honeypot
            "username": username,
            "email": "somethingelse@example.biz",
            "terms": True,
        }
        response = self.client.post(self.signup_url, data=data)
        assert response.status_code == 400

    def test_clashing_username(self):
        """First a GitHub user exists. Then a Google user tries to sign up
        whose email address, when `email.split('@')[0]` would become the same
        as the existing GitHub user.
        """
        user(username="octocat", save=True)
        self.google_login(
            profile_data=dict(self.google_profile_data, email="octocat@gmail.com",)
        )
        response = self.client.get(self.signup_url)
        assert response.status_code == 200
        doc = pq(response.content)
        assert doc.find('input[name="username"]').val() == "octocat2"

    def test_signup_username_error_event_tracking(self):
        """
        Tests that GA tracking events are sent for errors in the username
        field submitted when signing-up with a new account.
        """
        user(username="octocat", save=True)
        with self.settings(
            GOOGLE_ANALYTICS_ACCOUNT="UA-XXXX-1",
            GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS=True,
        ):
            p1 = mock.patch("kuma.users.signal_handlers.track_event")
            p2 = mock.patch("kuma.users.views.track_event")
            p3 = mock.patch("kuma.users.providers.google.views.track_event")
            with p1 as track_event_mock_signals, p2 as track_event_mock_views, p3 as track_event_mock_google:

                self.google_login(
                    headers={
                        # Needed to trigger the 'auth-started' GA tracking event.
                        "HTTP_REFERER": "http://testserver/en-US/"
                    }
                )

                data = {
                    "website": "",
                    "username": "octocat",
                    "email": "octocat-private@example.com",
                    "terms": True,
                    "is_newsletter_subscribed": True,
                }
                response = self.client.post(self.signup_url, data=data)
                assert response.status_code == 200

                track_event_mock_signals.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_SUCCESSFUL, "google"
                )
                track_event_mock_google.assert_called_with(
                    CATEGORY_SIGNUP_FLOW, ACTION_AUTH_STARTED, "google"
                )
                track_event_mock_views.assert_has_calls(
                    [
                        mock.call(CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_AUDIT, "google"),
                        mock.call(
                            CATEGORY_SIGNUP_FLOW, ACTION_PROFILE_EDIT_ERROR, "username"
                        ),
                    ]
                )


def test_delete_user_login_always_required(db, client):
    # Anonymous client gets redirected to sign in page.
    url = reverse("users.user_delete", kwargs={"username": "missing"})
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert reverse("account_login") in response["Location"]


def test_delete_user_not_allowed(db, user_client, wiki_user_2):
    # A username that doesn't exist.
    url = reverse("users.user_delete", kwargs={"username": "missing"})
    response = user_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404

    # Attempting to delete someone else.
    url = reverse("users.user_delete", kwargs={"username": wiki_user_2.username})
    response = user_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403


def test_delete_user_with_no_revisions(db, user_client, wiki_user):
    # sanity check fixtures
    assert not Revision.objects.filter(creator=wiki_user).exists()
    assert not AttachmentRevision.objects.filter(creator=wiki_user).exists()
    url = reverse("users.user_delete", kwargs={"username": wiki_user.username})
    response = user_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    response = user_client.post(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert not User.objects.filter(username=wiki_user.username).exists()


def test_delete_user_no_revisions_misc_related(db, user_client, wiki_user):
    Key.objects.create(user=wiki_user)
    revision_akismet_submission = RevisionAkismetSubmission.objects.create(
        sender=wiki_user, type="spam"
    )
    document_deletion_log = DocumentDeletionLog.objects.create(
        locale="any", slug="Any/Thing", user=wiki_user, reason="..."
    )
    document_spam_attempt_user = DocumentSpamAttempt.objects.create(user=wiki_user,)
    throwaway_user = User.objects.create(username="throwaway")
    document_spam_attempt_reviewer = DocumentSpamAttempt.objects.create(
        user=throwaway_user, reviewer=wiki_user,
    )
    user_ban_by = UserBan.objects.create(user=throwaway_user, by=wiki_user)
    user_ban_user = UserBan.objects.create(
        user=wiki_user,
        by=throwaway_user,
        is_active=False,  # otherwise it logs the user out
    )

    url = reverse("users.user_delete", kwargs={"username": wiki_user.username})
    response = user_client.post(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert not User.objects.filter(username=wiki_user.username).exists()

    # These are plainly deleted
    assert not Key.objects.all().exists()

    # Moved to anonymous user
    revision_akismet_submission.refresh_from_db()
    assert revision_akismet_submission.sender.username == "Anonymous"
    document_deletion_log.refresh_from_db()
    assert document_deletion_log.user.username == "Anonymous"
    document_spam_attempt_user.refresh_from_db()
    assert document_spam_attempt_user.user.username == "Anonymous"
    document_spam_attempt_reviewer.refresh_from_db()
    assert document_spam_attempt_reviewer.reviewer.username == "Anonymous"
    user_ban_by.refresh_from_db()
    assert user_ban_by.by.username == "Anonymous"
    user_ban_user.refresh_from_db()
    assert user_ban_user.user.username == "Anonymous"


def test_delete_user_donate_attributions(
    db, user_client, wiki_user, wiki_user_github_account, root_doc
):
    revision = root_doc.revisions.first()
    # Sanity check the fixture
    assert revision.creator == wiki_user

    RevisionAkismetSubmission.objects.create(sender=wiki_user)

    attachment_revision = AttachmentRevision(
        attachment=Attachment.objects.create(title="test attachment"),
        file="some/path.ext",
        mime_type="application/kuma",
        creator=wiki_user,
        title="test attachment",
    )
    attachment_revision.save()
    assert AttachmentRevision.objects.filter(creator=wiki_user).exists()

    url = reverse("users.user_delete", kwargs={"username": wiki_user.username})
    response = user_client.post(
        url, {"attributions": "donate"}, HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 302
    assert not User.objects.filter(username=wiki_user.username).exists()
    with pytest.raises(SocialAccount.DoesNotExist):
        wiki_user_github_account.refresh_from_db()

    revision.refresh_from_db()
    assert revision.creator.username == "Anonymous"

    attachment_revision.refresh_from_db()
    assert attachment_revision.creator.username == "Anonymous"

    # The user_client should now become "invalid" since its session
    # is going to point to no user.
    response = user_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert reverse("account_login") in response["Location"]
    # Let's doublecheck that
    whoami_url = reverse("api.v1.whoami")
    response = user_client.get(whoami_url)
    assert response.status_code == 200
    assert "username" not in response.json()
    assert "is_authenticated" not in response.json()


@mock.patch("kuma.users.signal_handlers.cancel_stripe_customer_subscriptions")
def test_delete_user_donate_attributions_and_cancel_subscriptions(
    mocked_cancel_stripe_customer_subscriptions, db, user_client, stripe_user, root_doc,
):
    UserSubscription.set_active(stripe_user, "sub_1234")

    url = reverse("users.user_delete", kwargs={"username": stripe_user.username})
    response = user_client.post(
        url, {"attributions": "donate"}, HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 302
    assert not User.objects.filter(username=stripe_user.username).exists()
    assert not UserSubscription.objects.filter(stripe_subscription_id="sub_1234")


def test_delete_user_keep_attributions(
    db, user_client, wiki_user, wiki_user_github_account, root_doc
):
    # Also, pretend that the user has a rich profile
    User.objects.filter(id=wiki_user.id).update(
        first_name="Peter",
        last_name="B",
        timezone="Ocean",
        locale="sv-SE",
        homepage="https://www.peterbe.com",
        title="Web Dev",
        fullname="Peter B",
        organization="Mozilla",
        location="Earth",
        bio="Doing stuff",
        irc_nickname="pb",
        website_url="https://www.peterbe.com",
        github_url="github/peterbe",
        mozillians_url="mozillians/peterbe",
        twitter_url="twitter/peterbe",
        linkedin_url="linkedin/peterbe",
        facebook_url="facebook/peterbe",
        stackoverflow_url="stackoverflow/peterbe",
        discourse_url="discourse/peterbe",
        # There's a whole test dedicated to this being something not-empty.
        stripe_customer_id="",
    )

    revision = root_doc.revisions.first()
    # Sanity check the fixture
    assert revision.creator == wiki_user

    attachment_revision = AttachmentRevision(
        attachment=Attachment.objects.create(title="test attachment"),
        file="some/path.ext",
        mime_type="application/kuma",
        creator=wiki_user,
        title="test attachment",
    )
    attachment_revision.save()
    assert AttachmentRevision.objects.filter(creator=wiki_user).exists()

    # Create some social logins
    assert SocialAccount.objects.filter(user=wiki_user).exists()

    # Create a RevisionAkismetSubmission
    RevisionAkismetSubmission.objects.create(
        revision=revision, sender=wiki_user, type="ham"
    )

    # Create an authentication key
    Key.objects.create(user=wiki_user)

    url = reverse("users.user_delete", kwargs={"username": wiki_user.username})
    response = user_client.post(
        url, {"attributions": "keep"}, HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 302
    # Should still exist
    assert User.objects.filter(username=wiki_user.username).exists()
    with pytest.raises(SocialAccount.DoesNotExist):
        wiki_user_github_account.refresh_from_db()

    # Should still be associated with the user
    revision.refresh_from_db()
    assert revision.creator.username == wiki_user.username
    attachment_revision.refresh_from_db()
    assert attachment_revision.creator.username == wiki_user.username

    # But the account should be clean, apart from the username.
    wiki_user.refresh_from_db()
    assert wiki_user.email == ""
    assert wiki_user.first_name == ""
    assert wiki_user.last_name == ""
    assert wiki_user.timezone == ""
    assert wiki_user.locale == ""
    assert wiki_user.homepage == ""
    assert wiki_user.title == ""
    assert wiki_user.fullname == ""
    assert wiki_user.organization == ""
    assert wiki_user.location == ""
    assert wiki_user.bio == ""
    assert wiki_user.irc_nickname == ""
    assert wiki_user.website_url == ""
    assert wiki_user.github_url == ""
    assert wiki_user.mozillians_url == ""
    assert wiki_user.twitter_url == ""
    assert wiki_user.linkedin_url == ""
    assert wiki_user.facebook_url == ""
    assert wiki_user.stackoverflow_url == ""
    assert wiki_user.discourse_url == ""
    assert wiki_user.stripe_customer_id == ""

    assert not SocialAccount.objects.filter(user=wiki_user).exists()

    # The user_client should now become "invalid" since its session
    # is going to point to no user.
    response = user_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert reverse("account_login") in response["Location"]
    # Let's doublecheck that
    whoami_url = reverse("api.v1.whoami")
    response = user_client.get(whoami_url)
    assert response.status_code == 200
    assert "username" not in response.json()
    assert "is_authenticated" not in response.json()

    # There should be no Key left
    assert not Key.objects.all().exists()


@mock.patch("kuma.users.stripe_utils.stripe")
def test_delete_user_keep_attributions_and_cancel_subscriptions(
    mocked_stripe, db, user_client, wiki_user, wiki_user_github_account, root_doc,
):
    subscription_id = "sub_1234"
    mock_subscription = mock.MagicMock()
    mock_subscription.id = subscription_id
    mock_customer = mock.MagicMock()
    mock_customer.subscriptions.data.__iter__.return_value = [mock_subscription]
    mocked_stripe.Customer.retrieve.return_value = mock_customer
    mocked_stripe.Subscription.retrieve.return_value = mock_subscription

    # Also, pretend that the user has a rich profile
    User.objects.filter(id=wiki_user.id).update(stripe_customer_id="cus_12345")
    UserSubscription.set_active(wiki_user, subscription_id)

    revision = root_doc.revisions.first()
    # Sanity check the fixture
    assert revision.creator == wiki_user

    url = reverse("users.user_delete", kwargs={"username": wiki_user.username})
    response = user_client.post(
        url, {"attributions": "keep"}, HTTP_HOST=settings.WIKI_HOST
    )
    assert response.status_code == 302
    # Should still exist
    assert User.objects.filter(username=wiki_user.username).exists()
    user_subscription = UserSubscription.objects.get(
        stripe_subscription_id=subscription_id
    )
    assert user_subscription.canceled


def test_delete_user_no_revisions_but_attachment_revisions_donate(
    db, user_client, wiki_user, django_user_model
):
    """
    This test is based on the bug report
    https://github.com/mdn/kuma/issues/6479

    The user didn't have any revisions to confront the legacy of, but there might be
    other things attached to the user.
    """
    assert not Revision.objects.filter(creator=wiki_user).exists()

    attachment_revision = AttachmentRevision(
        attachment=Attachment.objects.create(title="test attachment"),
        file="some/path.ext",
        mime_type="application/kuma",
        creator=wiki_user,
        title="test attachment",
    )
    attachment_revision.save()
    url = reverse("users.user_delete", kwargs={"username": wiki_user.username})
    response = user_client.post(url, HTTP_HOST=settings.WIKI_HOST)
    # This means it didn't work! The form rejects.
    assert response.status_code == 200

    # Ok, let's donate the attachment revisions to "Anonymous"
    response = user_client.post(
        url, {"attributions": "donate"}, HTTP_HOST=settings.WIKI_HOST
    )
    # This means it worked! The user's attributions have been donated to the Anonymous user.
    assert response.status_code == 302

    with pytest.raises(User.DoesNotExist):
        wiki_user.refresh_from_db()

    attachment_revision.refresh_from_db()
    assert attachment_revision.creator.username == "Anonymous"


@pytest.mark.parametrize(
    "email, expected_status",
    [("test@example.com", 302), ("not an email", 400)],
    ids=("good_email", "bad_email"),
)
def test_send_recovery_email(db, client, email, expected_status):
    url = reverse("users.send_recovery_email")
    response = client.post(url, {"email": email})
    assert response.status_code == expected_status
    assert_no_cache_header(response)
    if expected_status == 302:
        assert response["Location"].endswith(reverse("users.recovery_email_sent"))


def test_recover_valid(wiki_user, client):
    recover_url = wiki_user.get_recovery_url()
    response = client.get(recover_url)
    assert response.status_code == 302
    assert_no_cache_header(response)
    assert response["Location"].endswith(reverse("users.recover_done"))


def test_invalid_token_fails(wiki_user, client):
    recover_url = wiki_user.get_recovery_url()
    bad_last_char = "2" if recover_url[-1] == "3" else "3"
    bad_recover_url = recover_url[:-1] + bad_last_char
    response = client.get(bad_recover_url)
    assert b"This link is no longer valid." in response.content


def test_invalid_uid_fails(wiki_user, client):
    # Make a recovery URL for a user that no longer exists.
    bad_recover_url = wiki_user.get_recovery_url()
    wiki_user.delete()
    response = client.get(bad_recover_url)
    assert response.status_code == 200
    assert_no_cache_header(response)
    assert b"This link is no longer valid." in response.content


def test_signin_landing(db, client, settings):
    response = client.get(reverse(settings.LOGIN_URL))
    github_login_url = "/users/github/login/"
    google_login_url = "/users/google/login/"
    # first, make sure that the page loads
    assert response.status_code == 200
    doc = pq(response.content)
    # ensure that both auth buttons are present
    assert doc(".auth-button-container a").length == 2
    # ensure each button links to the appropriate endpoint
    assert doc(".github-auth").attr.href == github_login_url
    assert doc(".google-auth").attr.href == google_login_url
    # just to be absolutely clear, there is no ?next=... on *this* page
    assert "next" not in doc(".github-auth").attr.href
    assert "next" not in doc(".google-auth").attr.href


def test_signin_landing_next(db, client, settings):
    """Going to /en-US/users/account/signup-landing?next=THIS should pick put
    that 'THIS' and put it into the Google and GitHub auth links."""
    next_page = "/en-US/Foo/Bar"
    response = client.get(reverse(settings.LOGIN_URL), {"next": next_page})
    assert response.status_code == 200
    doc = pq(response.content)
    github_login_url = "/users/github/login/"
    google_login_url = "/users/google/login/"
    next = f"?{urlencode({'next': next_page})}"
    assert doc(".github-auth").attr.href == github_login_url + next
    assert doc(".google-auth").attr.href == google_login_url + next


def test_next_paramter_in_auth_links(db, client, root_doc):
    """View any other page and observe that the auth links (they're part of the
    auth modal) have a ?next= link on them."""
    url = root_doc.get_absolute_url()
    response = client.get(url)
    assert response.status_code == 200
    doc = pq(response.content)
    github_login_url = "/users/github/login/"
    google_login_url = "/users/google/login/"
    next = f"?{urlencode({'next': url})}"
    assert doc(".github-auth").attr.href == github_login_url + next
    assert doc(".google-auth").attr.href == google_login_url + next
