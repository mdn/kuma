import requests_mock
from django.contrib.admin import AdminSite
from django.test import RequestFactory

from kuma.users.models import User
from kuma.users.tests import UserTestCase

from . import document, revision
from ..admin import DocumentSpamAttemptAdmin, SUBMISSION_NOT_AVAILABLE
from ..models import DocumentSpamAttempt


class DocumentSpamAttemptAdminTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ["wiki/documents.json"]
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
        self.user = User.objects.get(username="testuser01")
        self.admin_user = User.objects.get(username="admin")
        self.request = RequestFactory().get("/admin/dsa")
        self.request.user = self.admin_user
        # Enable admin's message_user
        self.request.session = {}
        self.get_messages(self.request)

    def test_title_short(self):
        dsa = DocumentSpamAttempt(title="A short title")
        assert self.admin.title_short(dsa) == "A short title"
        dsa.title = "A long title that will need to be truncated."
        assert self.admin.title_short(dsa) == "A long title that will n…"

    def test_slug_short(self):
        dsa = DocumentSpamAttempt(slug="Web/CSS")
        assert self.admin.slug_short(dsa) == "Web/CSS"
        dsa.slug = "Web/A_long_slug_that_will_be_truncated"
        assert self.admin.slug_short(dsa) == "Web/A_long_slug_that_wil…"

    def test_doc_short_without_document(self):
        dsa = DocumentSpamAttempt(slug="Slug")
        assert self.admin.doc_short(dsa) == "<em>new document</em>"

    def test_doc_short_short_slug_and_title(self):
        slug = "NotSpam"
        html = "<p>This page is not spam.</p>"
        doc = document(title="blah", slug=slug, html=html, save=True)
        revision(document=doc, content=html, is_approved=True, save=True)
        dsa = DocumentSpamAttempt(slug=slug, document=doc)
        assert self.admin.doc_short(dsa) == "/en-US/docs/NotSpam (blah)"
        assert self.admin.doc_short(dsa) == str(doc)

    def test_doc_short_long_slug_and_title(self):
        slug = "Web/Guide/HTML/Sections_and_Outlines_of_an_HTML5_document"
        title = "Sections and Outlines of an HTML5 Document"
        html = "<p>This German page is not spam.</p>"
        doc = document(title=title, slug=slug, html=html, save=True, locale="de")
        revision(document=doc, content=html, is_approved=True, save=True)
        dsa = DocumentSpamAttempt(slug=slug, document=doc)
        expected = "/de/docs/Web/Guide/HTML/… (Sections and Outlines of…)"
        assert self.admin.doc_short(dsa) == expected

    def test_doc_short_long_unicode(self):
        slug = "Web/Guide/HTML/HTML5_ডকুমেন্টের_সেকশন_এবং_আউটলাইন"
        title = "HTML5 ডকুমেন্টের সেকশন এবং আউটলাইন"
        html = "<p>This Bengali page is not spam.</p>"
        doc = document(title=title, slug=slug, html=html, save=True, locale="bn")
        revision(document=doc, content=html, is_approved=True, save=True)
        dsa = DocumentSpamAttempt(slug=slug, document=doc)
        expected = "/bn/docs/Web/Guide/HTML/… (HTML5 ডকুমেন্টের সেকশন এব…)"
        assert self.admin.doc_short(dsa) == expected

    def test_submitted_data(self):
        dsa = DocumentSpamAttempt(data=None)
        assert self.admin.submitted_data(dsa) == SUBMISSION_NOT_AVAILABLE
        data = '{"foo": "bar"}'
        dsa.data = data
        expected = "\n".join(("<dl>", "  <dt>foo</dt><dd>bar</dd>", "</dl>"))
        assert self.admin.submitted_data(dsa) == expected

    def assert_needs_review(self):
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.NEEDS_REVIEW
        assert dsa.reviewer is None
        assert dsa.reviewed is None

    @requests_mock.mock()
    def test_save_no_review(self, mock_requests):
        dsa = DocumentSpamAttempt(
            user=self.user, title="Not reviewed", slug="test/spam"
        )
        assert not DocumentSpamAttempt.objects.exists()
        self.admin.save_model(self.request, dsa, None, True)
        self.assert_needs_review()

    @requests_mock.mock()
    def test_save_no_data(self, mock_requests):
        dsa = DocumentSpamAttempt(
            user=self.user,
            title="No data",
            slug="test/spam",
            review=DocumentSpamAttempt.HAM,
        )
        assert not DocumentSpamAttempt.objects.exists()
        self.admin.save_model(self.request, dsa, None, True)
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.HAM
        assert dsa.reviewer == self.admin_user
        assert dsa.reviewed is not None

    @requests_mock.mock()
    def test_save_confirm_spam(self, mock_requests):
        dsa = DocumentSpamAttempt(
            user=self.user,
            title="Confirmed as Spam",
            slug="test/spam",
            data=self.sample_data,
            review=DocumentSpamAttempt.SPAM,
        )
        assert not DocumentSpamAttempt.objects.exists()
        self.admin.save_model(self.request, dsa, None, True)
        dsa = DocumentSpamAttempt.objects.get()
        assert dsa.review == DocumentSpamAttempt.SPAM
        assert dsa.reviewer == self.admin_user
        assert dsa.reviewed is not None
