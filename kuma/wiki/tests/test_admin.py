import pytest
from pyquery import PyQuery as pq

from constance.test import override_config
from django.contrib.admin import AdminSite
from django.test import RequestFactory
import requests_mock
from waffle.models import Flag

from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.spam.akismet import Akismet
from kuma.spam.constants import HAM_URL, SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL
from kuma.users.tests import UserTestCase
from kuma.users.models import User
from kuma.wiki.admin import DocumentSpamAttemptAdmin
from kuma.wiki.models import DocumentSpamAttempt, RevisionAkismetSubmission


@pytest.mark.spam
class DocumentSpamAttemptAdminTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']
    sample_data = """{
        "blog_lang": "en_us",
        "comment_type": "wiki-revision",
        "referrer": "https://developer.mozilla.org/en-US/docs/new?slug=Web/CSS",
        "user_ip": "192.168.10.1",
        "blog_charset": "UTF-8",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3)",
        "comment_content": "Web_CSS\\nWeb_CSS\\n\\n<p>spam</p>\\nComment\\n\\n",
        "comment_author": "viagra-test-123",
        "comment_author_email": "viagra-test-123@example.com"
    }"""

    def setUp(self):
        self.admin = DocumentSpamAttemptAdmin(DocumentSpamAttempt, AdminSite())
        self.user = User.objects.get(username='testuser01')
        self.admin_user = User.objects.get(username='admin')
        self.request = RequestFactory().get('/admin/dsa')
        self.request.user = self.admin_user
        # Enable admin's message_user
        self.request.session = {}
        self.get_messages(self.request)

    def test_title_short(self):
        dsa = DocumentSpamAttempt(title='A short title')
        assert self.admin.title_short(dsa) == 'A short title'
        dsa.title = 'A long title that will need to be truncated.'
        assert self.admin.title_short(dsa) == 'A long title that will...'

    def test_slug_short(self):
        dsa = DocumentSpamAttempt(slug='Web/CSS')
        assert self.admin.slug_short(dsa) == 'Web/CSS'
        dsa.slug = 'Web/A_long_slug_that_will_be_truncated'
        assert self.admin.slug_short(dsa) == 'Web/A_long_slug_that_w...'''

    def test_submitted_data(self):
        dsa = DocumentSpamAttempt(data=None)
        expected = self.admin.SUBMISSION_NOT_AVAILABLE
        assert self.admin.submitted_data(dsa) == expected
        dsa.data = '{"foo": "bar"}'
        assert self.admin.submitted_data(dsa) == (
            '{\n'
            '    "foo": "bar"\n'
            '}')

    def assert_needs_review(self):
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.NEEDS_REVIEW
        assert dsa.reviewer is None
        assert dsa.reviewed is None

    @requests_mock.mock()
    def test_save_no_review(self, mock_requests):
        dsa = DocumentSpamAttempt(user=self.user,
                                  title='Not reviewed',
                                  slug='test/spam')
        assert not DocumentSpamAttempt.objects.exists()
        self.admin.save_model(self.request, dsa, None, True)
        self.assert_needs_review()

    @requests_mock.mock()
    def test_save_no_data(self, mock_requests):
        dsa = DocumentSpamAttempt(user=self.user,
                                  title='No data',
                                  slug='test/spam',
                                  review=DocumentSpamAttempt.HAM)
        assert not DocumentSpamAttempt.objects.exists()
        self.admin.save_model(self.request, dsa, None, True)
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.HAM
        assert dsa.reviewer == self.admin_user
        assert dsa.reviewed is not None

    @requests_mock.mock()
    def test_save_confirm_spam(self, mock_requests):
        dsa = DocumentSpamAttempt(user=self.user,
                                  title='Confirmed as Spam',
                                  slug='test/spam',
                                  data=self.sample_data,
                                  review=DocumentSpamAttempt.SPAM)
        assert not DocumentSpamAttempt.objects.exists()
        self.admin.save_model(self.request, dsa, None, True)
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.SPAM
        assert dsa.reviewer == self.admin_user
        assert dsa.reviewed is not None

    @override_config(AKISMET_KEY='admin')
    @requests_mock.mock()
    def test_save_false_positive(self, mock_requests):
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(self.admin_user)
        dsa = DocumentSpamAttempt(user=self.user,
                                  title='No data',
                                  slug='test/spam',
                                  data=self.sample_data,
                                  review=DocumentSpamAttempt.HAM)
        assert not DocumentSpamAttempt.objects.exists()
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(HAM_URL, content=Akismet.submission_success)
        self.admin.save_model(self.request, dsa, None, True)
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.HAM
        assert dsa.reviewer == self.admin_user
        assert dsa.reviewed is not None

    @override_config(AKISMET_KEY='')
    @requests_mock.mock()
    def test_save_false_positive_no_akismet(self, mock_requests):
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(self.admin_user)
        dsa = DocumentSpamAttempt(user=self.user,
                                  title='No data',
                                  slug='test/spam',
                                  data=self.sample_data,
                                  review=DocumentSpamAttempt.HAM)
        assert not DocumentSpamAttempt.objects.exists()
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(HAM_URL, content=Akismet.submission_success)
        self.admin.save_model(self.request, dsa, None, True)
        self.assert_needs_review()

    @override_config(AKISMET_KEY='admin')
    @requests_mock.mock()
    def test_save_false_positive_no_submission_flag(self, mock_requests):
        dsa = DocumentSpamAttempt(user=self.user,
                                  title='No data',
                                  slug='test/spam',
                                  data=self.sample_data,
                                  review=DocumentSpamAttempt.HAM)
        assert not DocumentSpamAttempt.objects.exists()
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(HAM_URL, content=Akismet.submission_success)
        self.admin.save_model(self.request, dsa, None, True)
        self.assert_needs_review()


@pytest.mark.spam
@override_config(AKISMET_KEY='admin')
class RevisionAkismetSubmissionAdminTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_spam_submission_filled(self):
        admin = User.objects.get(username='admin')
        revision = admin.created_revisions.all()[0]
        url = urlparams(
            reverse('admin:wiki_revisionakismetsubmission_add'),
            revision=revision.id,
            type='ham',
        )
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        page = pq(response.content)
        revision_inputs = page.find('input#id_revision')
        self.assertEqual(len(revision_inputs), 1)
        self.assertEqual(revision_inputs[0].value, str(revision.id))

        type_inputs = page.find('input[name=type]')
        self.assertEqual(len(type_inputs), 2)

        for type_input in type_inputs:
            if type_input.value == 'spam':
                self.assertTrue(not type_input.checked)
            elif type_input.value == 'ham':
                self.assertTrue(type_input.checked)

    @requests_mock.mock()
    def test_spam_submission_submitted(self, mock_requests):
        admin = User.objects.get(username='admin')
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(admin)
        revision = admin.created_revisions.all()[0]
        url = reverse('admin:wiki_revisionakismetsubmission_add')

        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(SPAM_URL, content=Akismet.submission_success)

        revision = admin.created_revisions.all()[0]
        data = {
            'revision': revision.id,
            'type': 'spam',
        }
        self.client.login(username='admin', password='testpass')
        url = reverse('admin:wiki_revisionakismetsubmission_add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # successfully created the submission record
        submission = RevisionAkismetSubmission.objects.first()
        self.assertTrue(submission is not None)
        self.assertEqual(submission.sender, admin)
        self.assertTrue(submission.sent)
        self.assertEqual(submission.revision, revision)
        self.assertEqual(submission.type, 'spam')

        self.assertEqual(mock_requests.call_count, 2)
        request_body = mock_requests.request_history[1].body
        self.assertIn('user_ip=0.0.0.0', request_body)
        self.assertIn('user_agent=', request_body)
        self.assertIn(revision.slug, request_body)
