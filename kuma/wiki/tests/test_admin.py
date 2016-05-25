# -*- coding: utf-8 -*-
import pytest
from pyquery import PyQuery as pq

from constance.test import override_config
from django.contrib.admin import AdminSite
from django.test import RequestFactory
from django.utils.six.moves.urllib.parse import parse_qsl
import requests_mock
from waffle.models import Flag

from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.spam.akismet import Akismet
from kuma.spam.constants import HAM_URL, SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL
from kuma.users.tests import UserTestCase
from kuma.users.models import User
from kuma.wiki.admin import DocumentSpamAttemptAdmin, SUBMISSION_NOT_AVAILABLE
from kuma.wiki.models import (DocumentSpamAttempt, RevisionAkismetSubmission,
                              RevisionIP)
from kuma.wiki.tests import document, revision


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

    def test_doc_short_without_document(self):
        dsa = DocumentSpamAttempt(slug='Slug')
        assert self.admin.doc_short(dsa) == '<em>new document</em>'

    def test_doc_short_short_slug_and_title(self):
        slug = 'NotSpam'
        html = '<p>This page is not spam.</p>'
        doc = document(title='blah', slug=slug, html=html, save=True)
        revision(document=doc, content=html, is_approved=True, save=True)
        dsa = DocumentSpamAttempt(slug=slug, document=doc)
        assert self.admin.doc_short(dsa) == u'/en-US/docs/NotSpam (blah)'
        assert self.admin.doc_short(dsa) == str(doc)

    def test_doc_short_long_slug_and_title(self):
        slug = 'Web/Guide/HTML/Sections_and_Outlines_of_an_HTML5_document'
        title = 'Sections and Outlines of an HTML5 Document'
        html = '<p>This German page is not spam.</p>'
        doc = document(title=title, slug=slug, html=html, save=True,
                       locale='de')
        revision(document=doc, content=html, is_approved=True, save=True)
        dsa = DocumentSpamAttempt(slug=slug, document=doc)
        expected = u'/de/docs/Web/Guide/HTML/… (Sections and Outlines of…)'
        assert self.admin.doc_short(dsa) == expected

    def test_doc_short_long_unicode(self):
        slug = u'Web/Guide/HTML/HTML5_ডকুমেন্টের_সেকশন_এবং_আউটলাইন'
        title = u'HTML5 ডকুমেন্টের সেকশন এবং আউটলাইন'
        html = '<p>This Bengali page is not spam.</p>'
        doc = document(title=title, slug=slug, html=html, save=True,
                       locale='bn-BD')
        revision(document=doc, content=html, is_approved=True, save=True)
        dsa = DocumentSpamAttempt(slug=slug, document=doc)
        expected = u'/bn-BD/docs/Web/Guide/HT… (HTML5 ডকুমেন্টের সেকশন এব…)'
        assert self.admin.doc_short(dsa) == expected

    def test_submitted_data(self):
        dsa = DocumentSpamAttempt(data=None)
        assert self.admin.submitted_data(dsa) == SUBMISSION_NOT_AVAILABLE
        data = '{"foo": "bar"}'
        dsa.data = data
        assert self.admin.submitted_data(dsa) == data

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
        assert mock_requests.called
        assert mock_requests.call_count == 2

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
        query_pairs = parse_qsl(request_body)
        expected_content = (
            'Seventh revision of the article.\n'
            'article-with-revisions\n'
            'Seventh revision of the article.\n'
            'Seventh revision of the article.'
        )
        expected = [
            ('blog', 'http://testserver/'),
            ('blog_charset', 'UTF-8'),
            ('blog_lang', 'en_us'),
            ('comment_author', 'admin'),
            ('comment_content', expected_content),
            ('comment_type', 'wiki-revision'),
            ('permalink',
             'http://testserver/en-US/docs/article-with-revisions'),
            ('user_ip', '0.0.0.0')
        ]
        self.assertEqual(sorted(query_pairs), expected)

        assert mock_requests.called
        assert mock_requests.call_count == 2

    @requests_mock.mock()
    def test_spam_submission_tags(self, mock_requests):
        admin = User.objects.get(username='admin')
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(admin)
        revision = admin.created_revisions.all()[0]
        revision.tags = '"Banana" "Orange" "Apple"'
        revision.save()
        url = reverse('admin:wiki_revisionakismetsubmission_add')

        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(SPAM_URL, content=Akismet.submission_success)

        data = {
            'revision': revision.id,
            'type': 'spam',
        }
        self.client.login(username='admin', password='testpass')
        url = reverse('admin:wiki_revisionakismetsubmission_add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        request_body = mock_requests.request_history[1].body
        submitted_data = dict(parse_qsl(request_body))
        expected_content = (
            'Seventh revision of the article.\n'
            'article-with-revisions\n'
            'Seventh revision of the article.\n'
            'Seventh revision of the article.\n'
            'Apple\n'
            'Banana\n'
            'Orange'
        )
        self.assertEqual(submitted_data['comment_content'], expected_content)

    def test_create_no_revision(self):
        url = urlparams(
            reverse('admin:wiki_revisionakismetsubmission_add'),
            type='ham',
        )
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(SUBMISSION_NOT_AVAILABLE, response.content)

    def test_view_change_existing(self):
        admin = User.objects.get(username='admin')
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(admin)
        revision = admin.created_revisions.all()[0]
        submission = RevisionAkismetSubmission.objects.create(
            sender=admin, revision=revision, type='ham')

        self.client.login(username='admin', password='testpass')
        url = reverse('admin:wiki_revisionakismetsubmission_change',
                      args=(submission.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(SUBMISSION_NOT_AVAILABLE, response.content)

    def test_view_change_with_data(self):
        admin = User.objects.get(username='admin')
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(admin)
        revision = admin.created_revisions.all()[0]
        submission = RevisionAkismetSubmission.objects.create(
            sender=admin, revision=revision, type='spam')
        RevisionIP.objects.create(revision=revision,
                                  data='{"content": "spam"}')

        self.client.login(username='admin', password='testpass')
        url = reverse('admin:wiki_revisionakismetsubmission_change',
                      args=(submission.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('{&quot;content&quot;: &quot;spam&quot;}',
                      response.content)

    def test_view_changelist_existing(self):
        admin = User.objects.get(username='admin')
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(admin)
        revision = admin.created_revisions.all()[0]
        RevisionAkismetSubmission.objects.create(sender=admin,
                                                 revision=revision,
                                                 type='ham')
        RevisionAkismetSubmission.objects.create(sender=admin,
                                                 type='ham')

        self.client.login(username='admin', password='testpass')
        url = reverse('admin:wiki_revisionakismetsubmission_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        revision_url = revision.get_absolute_url()
        self.assertIn(revision_url, response.content)
        self.assertIn('None', response.content)
