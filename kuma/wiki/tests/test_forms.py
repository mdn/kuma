from django import forms
from django.core import mail
from django.test import RequestFactory

import pytest
import requests_mock
from constance.test import override_config
from waffle.models import Flag

from kuma.spam.constants import CHECK_URL, SPAM_CHECKS_FLAG, VERIFY_URL
from kuma.users.tests import UserTestCase, UserTransactionTestCase

from ..constants import SPAM_EXEMPTED_FLAG
from ..forms import RevisionForm, TreeMoveForm
from ..models import DocumentSpamAttempt, Revision
from ..tests import normalize_html, revision


@override_config(AKISMET_KEY='forms')
class RevisionFormTests(UserTransactionTestCase):
    rf = RequestFactory()

    def setUp(self):
        super(RevisionFormTests, self).setUp()
        self.testuser = self.user_model.objects.get(username='testuser')
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': True},
        )

    def tearDown(self):
        super(RevisionFormTests, self).tearDown()
        Flag.objects.filter(name=SPAM_EXEMPTED_FLAG).delete()
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': None},
        )

    def test_form_onload_attr_filter(self):
        """
        RevisionForm should strip out any harmful onload attributes from
        input markup

        bug 821986
        """
        rev = revision(save=True, is_approved=True, content="""
            <svg><circle onload=confirm(3)>
        """)
        request = self.rf.get('/')
        rev_form = RevisionForm(instance=rev, request=request)
        self.assertNotIn('onload', rev_form.initial['content'])

    def test_form_loaded_with_section(self):
        """
        RevisionForm given section_id should load initial content for only
        one section
        """
        rev = revision(save=True, is_approved=True, content="""
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">s2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """)
        expected = """
            <h1 id="s2">s2</h1>
            <p>test</p>
            <p>test</p>
        """
        request = self.rf.get('/')
        rev_form = RevisionForm(instance=rev, section_id='s2', request=request)
        self.assertEqual(normalize_html(expected),
                         normalize_html(rev_form.initial['content']))

    @pytest.mark.spam
    @requests_mock.mock()
    def test_form_save_section(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content='false')
        rev = revision(save=True, is_approved=True, content="""
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">s2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """)
        replace_content = """
            <h1 id="s2">New stuff</h1>
            <p>new stuff</p>
        """
        expected = """
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">New stuff</h1>
            <p>new stuff</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """
        request = self.rf.get('/')
        request.user = rev.creator
        rev_form = RevisionForm(data={'content': replace_content},
                                instance=rev,
                                section_id='s2',
                                request=request)
        new_rev = rev_form.save(rev.document)
        self.assertEqual(normalize_html(expected),
                         normalize_html(new_rev.content))

    def test_form_rejects_empty_slugs_with_parent(self):
        """
        RevisionForm should reject empty slugs, even if there
        is a parent slug portion
        """
        data = {
            'slug': '',
            'title': 'Title',
            'content': 'Content',
        }
        request = self.rf.get('/')
        request.user = self.testuser
        rev_form = RevisionForm(data=data,
                                request=request,
                                parent_slug='User:groovecoder')
        self.assertFalse(rev_form.is_valid())

    @pytest.mark.spam
    @requests_mock.mock()
    def test_multiword_tags(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content='false')
        rev = revision(save=True)
        request = self.rf.get('/')
        request.user = rev.creator
        data = {
            'content': 'Content',
            'toc_depth': 1,
            'tags': '"MDN Meta"',
        }
        rev_form = RevisionForm(data=data, instance=rev, request=request)
        self.assertTrue(rev_form.is_valid())
        self.assertEqual(rev_form.cleaned_data['tags'], '"MDN Meta"')

    @pytest.mark.spam
    @requests_mock.mock()
    def test_case_sensitive_tags(self, mock_requests):
        """
        RevisionForm should reject new tags that are the same as existing tags
        that only differ by case.
        """
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content='false')
        rev = revision(save=True, tags='"JavaScript"')
        request = self.rf.get('/')
        request.user = rev.creator
        data = {
            'content': 'Content',
            'toc_depth': 1,
            'tags': 'Javascript',  # Note the lower-case "S".
        }
        rev_form = RevisionForm(data=data, instance=rev, request=request)
        self.assertTrue(rev_form.is_valid())
        self.assertEqual(rev_form.cleaned_data['tags'], '"JavaScript"')

    @pytest.mark.spam
    @requests_mock.mock()
    def test_akismet_enabled(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        request = self.rf.get('/')
        # using a non-admin user here to make sure we can test the
        # exmption rule below
        request.user = self.testuser
        data = {
            'slug': 'Title',
            'title': 'Title',
            'content': 'Content',
        }
        rev_form = RevisionForm(data=data, request=request)

        self.assertTrue(rev_form.akismet_enabled())

        # create the waffle flag and add the test user to it
        flag, created = Flag.objects.get_or_create(name=SPAM_EXEMPTED_FLAG)
        flag.users.add(self.testuser)

        # now disabled because the test user is exempted from the spam check
        self.assertFalse(rev_form.akismet_enabled())

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_ham(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content='false')  # false means it's ham
        request = self.rf.get('/')
        # using a non-admin user here to make sure we can test the
        # exmption rule below
        request.user = self.testuser
        data = {
            'title': 'Title',
            'slug': 'Slug',
            'content': 'Content',
            'toc_depth': Revision.TOC_DEPTH_ALL,
        }
        self.assertEqual(DocumentSpamAttempt.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        rev_form = RevisionForm(data=data, request=request)
        self.assertTrue(rev_form.is_valid())
        self.assertEqual(DocumentSpamAttempt.objects.count(), 0)

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_spam(self, mock_requests):
        self._test_akismet_error(mock_requests, 'true')

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_error(self, mock_requests):
        self._test_akismet_error(mock_requests, 'terrible')

    def _test_akismet_error(self, mock_requests, check_response):
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content=check_response)
        request = self.rf.get('/')
        # using a non-admin user here to make sure we can test the
        # exmption rule below
        request.user = self.testuser
        data = {
            'title': 'Title',
            'slug': 'Slug',
            'content': 'Content',
            'toc_depth': Revision.TOC_DEPTH_ALL,
        }
        self.assertEqual(DocumentSpamAttempt.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        rev_form = RevisionForm(data=data, request=request)
        self.assertFalse(rev_form.is_valid())
        self.assertTrue(DocumentSpamAttempt.objects.count() > 0)
        attempt = DocumentSpamAttempt.objects.latest()
        self.assertEqual(attempt.title, 'Title')
        self.assertEqual(attempt.slug, 'Slug')
        self.assertEqual(attempt.user, self.testuser)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(attempt.title, mail.outbox[0].body)
        self.assertIn(attempt.slug, mail.outbox[0].body)
        self.assertIn(attempt.user.username, mail.outbox[0].body)

        try:
            rev_form.clean()
        except forms.ValidationError as exc:
            self.assertHTMLEqual(exc.message, rev_form.akismet_error_message)

    @pytest.mark.spam
    @requests_mock.mock()
    def test_akismet_parameters(self, mock_requests):
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content='false')
        request = self.rf.get('/')
        request.user = self.testuser
        data = {
            'title': 'Title',
            'slug': 'Slug',
            'summary': 'Summary',
            'content': 'Content',
            'toc_depth': str(Revision.TOC_DEPTH_ALL),
            'comment': 'Comment',
            'tags': '"Tag1" "Tag2"',
            'keywords': 'HTML, CSS, JS',
        }
        rev_form = RevisionForm(data=data, request=request)
        self.assertTrue(rev_form.is_valid())
        parameters = rev_form.akismet_parameters()
        self.assertEqual(parameters['comment_author'], 'Test User')
        self.assertEqual(parameters['comment_author_email'],
                         self.testuser.email)
        # The content contains just
        for value in data.values():
            self.assertIn(value, parameters['comment_content'])
        self.assertEqual(parameters['comment_type'], 'wiki-revision')
        self.assertEqual(parameters['blog_lang'], 'en_us')
        self.assertEqual(parameters['blog_charset'], 'UTF-8')


class TreeMoveFormTests(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_form_properly_strips_leading_cruft(self):
        """
        Tests that leading slash, trailing slash, and {locale}/docs/
        are removed if included
        """
        comparisons = [
            ['/somedoc', 'somedoc'],  # leading slash
            ['/en-US/docs/mynewplace', 'mynewplace'],  # locale and docs
            ['/docs/one', 'one'],  # leading docs
            ['docs/one', 'one'],  # leading docs without slash
            ['fr/docs/one', 'one'],  # foreign locale with docs
            ['docs/article-title/docs', 'article-title/docs'],  # docs with later docs
            ['/en-US/docs/something/', 'something']  # trailing slash
        ]

        for comparison in comparisons:
            form = TreeMoveForm({'locale': 'en-US', 'title': 'Article',
                                 'slug': comparison[0]})
            form.is_valid()
            self.assertEqual(comparison[1], form.cleaned_data['slug'])

    def test_form_enforces_parent_doc_to_exist(self):
        form = TreeMoveForm({'locale': 'en-US', 'title': 'Article',
                             'slug': 'nothing/article'})
        form.is_valid()
        self.assertTrue(form.errors)
        self.assertIn(u'Parent', form.errors.as_text())
        self.assertIn(u'does not exist', form.errors.as_text())
