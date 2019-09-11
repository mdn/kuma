# -*- coding: utf-8 -*-
import json
import unicodedata

import pytest
import requests_mock
from constance.test import override_config
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import RequestFactory
from waffle.models import Flag
from waffle.testutils import override_flag, override_switch

from kuma.core.urlresolvers import reverse
from kuma.spam.constants import (CHECK_URL, SPAM_ADMIN_FLAG, SPAM_CHECKS_FLAG,
                                 SPAM_SPAMMER_FLAG, SPAM_TESTING_FLAG,
                                 VERIFY_URL)
from kuma.users.tests import UserTestCase

from ..constants import SPAM_TRAINING_SWITCH
from ..forms import AkismetHistoricalData, DocumentForm, RevisionForm, TreeMoveForm
from ..models import DocumentSpamAttempt, Revision, RevisionIP
from ..tests import document, normalize_html, revision


class AkismetHistoricalDataTests(UserTestCase):
    """Tests for AkismetHistoricalData."""
    rf = RequestFactory()
    base_akismet_payload = {
        'blog_charset': 'UTF-8',
        'blog_lang': u'en_us',
        'comment_author': u'Test User',
        'comment_author_email': u'testuser@test.com',
        'comment_content': (
            'Sample\n'
            'SampleSlug\n'
            'content\n'
            'Comment'
        ),
        'comment_type': 'wiki-revision',
        'referrer': '',
        'user_agent': '',
        'user_ip': '0.0.0.0'
    }

    def setUp(self):
        super(AkismetHistoricalDataTests, self).setUp()
        self.user = self.user_model.objects.get(username='testuser')
        self.revision = revision(save=True, content='content', title='Sample',
                                 slug='SampleSlug', comment='Comment',
                                 summary='', tags='')

    def test_no_revision_ip_no_request(self):
        """
        Test Akismet payload with no RevisionIP or request.

        This is a possible payload from ./manage.py submit_deleted_documents.
        """
        params = AkismetHistoricalData(self.revision).parameters
        assert params == self.base_akismet_payload

    def test_revision_ip_no_data(self):
        """
        Test Akismet payload with a RevisionIP without data.

        This is a possible payload from an April 2016 revision.
        """
        RevisionIP.objects.create(revision=self.revision, ip='127.0.0.1',
                                  user_agent='Agent', referrer='Referrer')
        request = self.rf.get('/en-US/dashboard/revisions')
        params = AkismetHistoricalData(self.revision, request).parameters
        expected = self.base_akismet_payload.copy()
        expected.update({
            'blog': 'http://testserver/',
            'permalink': 'http://testserver/en-US/docs/SampleSlug',
            'referrer': 'Referrer',
            'user_agent': 'Agent',
            'user_ip': '127.0.0.1',
        })
        assert params == expected

    def test_revision_ip_with_data(self):
        """
        Test Akismet payload is the data from the RevisionIP.

        This payload is from a revision after April 2016.
        """
        RevisionIP.objects.create(revision=self.revision, ip='127.0.0.1',
                                  user_agent='Agent', referrer='Referrer',
                                  data='{"content": "spammy"}')
        request = self.rf.get('/en-US/dashboard/revisions')
        params = AkismetHistoricalData(self.revision, request).parameters
        assert params == {'content': 'spammy'}


@pytest.mark.parametrize('content,expected', [
    ('<div onclick="alert(\'hacked!\')">click me</div>',
     '<div>click me</div>'),
    ('<svg><circle onload=confirm(3)>',
     '&lt;svg&gt;&lt;circle onload="confirm(3)"&gt;&lt;/circle&gt;&lt;/svg&gt;')
], ids=('strip', 'escape'))
def test_form_onload_attr_filter(root_doc, rf, content, expected):
    """
    For a RevisionForm created from an existing instance, the content should
    already have been bleached, so for example, any harmful on* attributes
    stripped or escaped (see bug 821986).
    """
    rev = root_doc.current_revision
    rev.content = content
    rev.save()
    request = rf.get('/')
    rev_form = RevisionForm(instance=rev, request=request)
    assert rev_form.initial['content'] == expected


def test_form_loaded_with_section(root_doc, rf):
    """
    RevisionForm given section_id should load initial content for only
    one section
    """
    rev = root_doc.current_revision
    rev.content = """
        <h1 id="s1">s1</h1>
        <p>test</p>
        <p>test</p>

        <h1 id="s2">s2</h1>
        <p>test</p>
        <p>test</p>

        <h1 id="s3">s3</h1>
        <p>test</p>
        <p>test</p>
    """
    rev.save()
    expected = """
        <h1 id="s2">s2</h1>
        <p>test</p>
        <p>test</p>
    """
    request = rf.get('/')
    rev_form = RevisionForm(instance=rev, section_id='s2', request=request)
    assert (normalize_html(expected) ==
            normalize_html(rev_form.initial['content']))


def test_form_save_section(root_doc, rf):
    rev = root_doc.current_revision
    rev.content = """
        <h1 id="s1">s1</h1>
        <p>test</p>
        <p>test</p>

        <h1 id="s2">s2</h1>
        <p>test</p>
        <p>test</p>

        <h1 id="s3">s3</h1>
        <p>test</p>
        <p>test</p>
    """
    rev.save()
    replace_content = """
        <h1 id="s2">New stuff</h1>
        <p>new stuff</p>
    """
    expected = """
        <h1 id="s1">s1</h1>
        <p>test</p>
        <p>test</p>

        <h1 id="New_stuff">New stuff</h1>
        <p>new stuff</p>

        <h1 id="s3">s3</h1>
        <p>test</p>
        <p>test</p>
    """
    request = rf.get('/')
    request.user = rev.creator
    rev_form = RevisionForm(data={'content': replace_content}, instance=rev,
                            section_id='s2', request=request)
    new_rev = rev_form.save(rev.document)
    assert normalize_html(expected) == normalize_html(new_rev.content)


def test_form_rejects_empty_slugs_with_parent(wiki_user, rf):
    """
    RevisionForm should reject empty slugs, even if there is a parent slug
    portion.
    """
    data = {
        'slug': '',
        'title': 'Title',
        'content': 'Content',
    }
    request = rf.get('/')
    request.user = wiki_user
    rev_form = RevisionForm(data=data,
                            request=request,
                            parent_slug='User:groovecoder')
    assert not rev_form.is_valid()


def test_multiword_tags(root_doc, rf):
    """ Multi-word tags should be handled. """
    rev = root_doc.current_revision
    request = rf.get('/')
    request.user = rev.creator
    data = {
        'content': 'Content',
        'toc_depth': 1,
        'tags': '"MDN Meta"',
    }
    rev_form = RevisionForm(data=data, instance=rev, request=request)
    assert rev_form.is_valid()
    assert rev_form.cleaned_data['tags'] == '"MDN Meta"'


def test_revision_form_normalize_unicode(root_doc, rf):
    """Revision slugs are normalized to NFKC, required for URLs."""

    raw_slug = u'Εφαρμογές'  # "Applications" in Greek (el)

    # In NFC / NFKD, 'έ' is represented by two "decomposed" codepoints
    #  03B5 (GREEK SMALL LETTER EPSILON)
    #  0301 (COMBINING ACUTE ACCENT)
    nfkd_slug = unicodedata.normalize('NFKD', raw_slug)

    # In NFC / NFKC, 'έ' is represented by a "composed" codepoint
    #  03AD (GREEK SMALL LETTER EPSILON WITH TONOS)
    nfkc_slug = unicodedata.normalize('NFKC', raw_slug)

    assert nfkd_slug != nfkc_slug

    rev = root_doc.current_revision
    request = rf.get('/')
    request.user = rev.creator
    data = {
        'content': 'Content',
        'toc_depth': 1,
        'slug': nfkd_slug
    }
    rev_form = RevisionForm(data=data, instance=rev, request=request)
    assert rev_form.is_valid()
    assert rev_form.cleaned_data['slug'] == nfkc_slug


def test_document_form_normalize_unicode(root_doc, rf):
    """Document slugs are normalized to NFC, required for URLs."""

    raw_slug = u'ফায়ারফক্স'  # "Firefox" in Bengali (bn)

    # This slug is the same in NFC, NFD, NFKD, and NFKD. The second character
    # has these codepoints:
    # 09af BENGALI LETTER YA (য)
    # 09bc BENGALI SIGN NUKTA
    # 09be BENGALI VOWEL SIGN AA (non-breaking spacing mark)
    nfkc_slug = u'\u09ab\u09be\u09af\u09bc\u09be\u09b0\u09ab\u0995\u09cd\u09b8'
    assert nfkc_slug == unicodedata.normalize('NFKC', raw_slug)

    # An alternate representation of the second character is:
    # 09df BENGALI LETTER YYA (য়)
    # 09be BENGALI VOWEL SIGN AA (non-breaking spacing mark)
    alt_slug = u'\u09ab\u09be\u09df\u09be\u09b0\u09ab\u0995\u09cd\u09b8'
    assert alt_slug != nfkc_slug

    rev = root_doc.current_revision
    request = rf.get('/')
    request.user = rev.creator
    data = {
        'slug': alt_slug,
        'title': root_doc.title,
        'locale': root_doc.locale
    }
    doc_form = DocumentForm(data=data, instance=root_doc)
    assert doc_form.is_valid()
    assert doc_form.cleaned_data['slug'] == nfkc_slug


def test_case_sensitive_tags(root_doc, rf):
    """
    RevisionForm should reject new tags that are the same as existing tags
    except that they only differ by case.
    """
    rev = root_doc.current_revision
    rev.tags = '"JavaScript"'
    rev.save()
    request = rf.get('/')
    request.user = rev.creator
    data = {
        'content': 'Content',
        'toc_depth': 1,
        'tags': 'Javascript',  # Note the lower-case "S".
    }
    rev_form = RevisionForm(data=data, instance=rev, request=request)
    assert rev_form.is_valid()
    assert rev_form.cleaned_data['tags'] == '"JavaScript"'


@override_config(AKISMET_KEY='forms')
class RevisionFormViewTests(UserTestCase):
    """Setup tests for RevisionForm as used in views."""
    rf = RequestFactory()
    akismet_keys = [  # Keys for a new English page or new translation
        'REMOTE_ADDR',
        'blog',
        'blog_charset',
        'blog_lang',
        'comment_author',
        'comment_author_email',
        'comment_content',
        'comment_type',
        'referrer',
        'user_agent',
        'user_ip',
    ]
    # Keys for a page edit (English or translation)
    akismet_keys_edit = sorted(akismet_keys + ['permalink'])

    def setUp(self):
        super(RevisionFormViewTests, self).setUp()
        self.testuser = self.user_model.objects.get(username='testuser')
        self.spam_checks_flag, created = Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': True},
        )

    def tearDown(self):
        super(RevisionFormViewTests, self).tearDown()
        self.spam_checks_flag.delete()


class RevisionFormEditTests(RevisionFormViewTests):
    """Test RevisionForm as used in edit view.

    Includes Akismet enabled, spam/ham, and training tests. These require a
    RevisionForm setup for POST validation, but are not unique to editing.
    """

    original = {  # Default attributes of original revision
        'content': (
            '<h2 id="Summary">Summary</h2>\n'
            '<p>The <strong><code>display</code></strong> CSS property'
            ' specifies the type of rendering box used for an element.</p>\n'
            '<p>{{cssinfo}}</p>\n'
            '<h2 id="Syntax">Syntax</h2>\n'
            '<pre class="brush:css">'
            'display: none;\n'
            '</pre>'
        ),
        'slug': 'Web/CSS/display',
        'tags': '"CSS" "CSS Property" "Reference"',
        'title': 'display',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }
    view_data_extra = {  # Extra data from view, derived from POST
        'form': 'rev',
        'content': (
            '<h2 id="Summary">Summary</h2>\n'
            '<p>The <strong><code>display</code></strong> CSS property'
            ' specifies the type of rendering box used for an element.</p>\n'
            '<p>{{cssinfo}} and my changes.</p>\n'
            '<h2 id="Syntax">Syntax</h2>\n'
            '<p><a href="http://spam.example.com">Buy my product!</a></p>\n'
            '<pre class="brush:css">display: none;</pre>\n'
        ),
        'comment': 'Comment',
        'days': '0',
        'hours': '0',
        'minutes': '0',
        'render_max_age': '0',
        'parent_id': '',
        'review_tags': [],
    }

    def setup_form(
            self, mock_requests, override_original=None, override_data=None,
            is_spam='false'):
        """
        Setup a RevisionForm for a POST to edit a page.

        Parameters:
        * mock_requests - Mockable requests for Akismet checks
        * override_original - Add or modify original revision
        * override_data - Add or modify the view data
        * is_spam - Response from the Akismet check-comment URL
        """
        revision(save=True, slug='Web')
        revision(save=True, slug='Web/CSS')
        original_params = self.original.copy()
        original_params.update(override_original or {})
        previous_revision = revision(save=True, **original_params)

        data = self.original.copy()
        data['current_rev'] = str(previous_revision.id)
        del data['slug']  # Not included in edit POST
        data.update(self.view_data_extra)
        data.update(override_data or {})

        request = self.rf.post('/en-US/docs/Web/CSS/display$edit')
        request.user = self.testuser

        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content=is_spam)

        section_id = None
        is_async_submit = False
        rev_form = RevisionForm(request=request,
                                data=data,
                                is_async_submit=is_async_submit,
                                section_id=section_id)
        rev_form.instance.document = previous_revision.document
        return rev_form

    @pytest.mark.spam
    @requests_mock.mock()
    def test_standard_edit(self, mock_requests):
        """Test Akismet parameters for edited English pages."""
        rev_form = self.setup_form(mock_requests)
        assert rev_form.is_valid(), rev_form.errors
        parameters = rev_form.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys_edit
        expected_content = (
            '<p>{{cssinfo}} and my changes.</p>\n'
            '<p><a href="http://spam.example.com">Buy my product!</a></p>\n'
            '<pre class="brush:css">display: none;</pre>\n'
            'Comment'
        )
        assert parameters['comment_content'] == expected_content
        assert parameters['comment_type'] == 'wiki-revision'
        assert parameters['blog'] == 'http://testserver/'
        assert parameters['blog_lang'] == 'en_us'
        assert parameters['blog_charset'] == 'UTF-8'
        assert parameters['REMOTE_ADDR'] == '127.0.0.1'
        assert parameters['permalink'] == ('http://testserver/en-US/docs/'
                                           'Web/CSS/display')

    @pytest.mark.spam
    @requests_mock.mock()
    def test_change_tags_edit(self, mock_requests):
        """
        Test Akismet parameters for edited legacy pages.

        Keywords and summary are included in the form if the legacy page
        includes them.
        """
        new_tags = '"CSS" "CSS Property" "Reference" "CSS Positioning"'
        rev_form = self.setup_form(mock_requests,
                                   override_data={'tags': new_tags})
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys_edit
        expected_content = (
            '<p>{{cssinfo}} and my changes.</p>\n'
            '<p><a href="http://spam.example.com">Buy my product!</a></p>\n'
            '<pre class="brush:css">display: none;</pre>\n'
            'Comment\n'
            'CSS Positioning'
        )
        assert parameters['comment_content'] == expected_content

    @pytest.mark.spam
    @requests_mock.mock()
    def test_legacy_edit(self, mock_requests):
        """
        Test Akismet parameters for edited legacy pages.

        Keywords and summary are included in the form if the legacy page
        includes them.
        """
        legacy_fields = {'keywords': 'CSS, display',
                         'summary': 'CSS property display'}
        extra_post_data = {'keywords': 'CSS display, hidden',
                           'summary': 'The CSS property display',
                           'comment': 'Updated'}
        rev_form = self.setup_form(mock_requests,
                                   override_original=legacy_fields,
                                   override_data=extra_post_data)
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys_edit
        expected_content = (
            'The CSS property display\n' +
            '<p>{{cssinfo}} and my changes.</p>\n'
            '<p><a href="http://spam.example.com">Buy my product!</a></p>\n'
            '<pre class="brush:css">display: none;</pre>\n'
            'Updated\n'
            'CSS display, hidden'
        )
        assert parameters['comment_content'] == expected_content

    @pytest.mark.spam
    @requests_mock.mock()
    def test_quoteless_tags(self, mock_requests):
        """
        Test Akismet parameters when the tags are saved without quotes.

        Tracked in bug 1268511.
        """
        tags = {'tags': 'CodingScripting, Glossary'}
        rev_form = self.setup_form(mock_requests, override_original=tags)
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys_edit
        expected_content = (
            '<p>{{cssinfo}} and my changes.</p>\n'
            '<p><a href="http://spam.example.com">Buy my product!</a></p>\n'
            '<pre class="brush:css">display: none;</pre>\n'
            'Comment\n'
            'CSS\n'
            'CSS Property\n'
            'Reference'
        )
        assert parameters['comment_content'] == expected_content

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_ham(self, mock_requests):
        assert DocumentSpamAttempt.objects.count() == 0
        assert len(mail.outbox) == 0
        rev_form = self.setup_form(mock_requests)
        assert rev_form.is_valid()
        assert DocumentSpamAttempt.objects.count() == 0

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_spam(self, mock_requests):
        assert DocumentSpamAttempt.objects.count() == 0
        assert len(mail.outbox) == 0
        rev_form = self.setup_form(mock_requests, is_spam='true')
        assert not rev_form.is_valid()
        assert rev_form.errors == {'__all__': [rev_form.akismet_error_message]}
        admin_path = reverse('admin:wiki_documentspamattempt_changelist')
        admin_url = admin_path
        assert admin_url not in rev_form.akismet_error_message

        assert DocumentSpamAttempt.objects.count() > 0
        attempt = DocumentSpamAttempt.objects.latest()
        assert attempt.title == 'display'
        assert attempt.slug == 'Web/CSS/display'
        assert attempt.user == self.testuser
        assert attempt.review == DocumentSpamAttempt.NEEDS_REVIEW
        assert attempt.data
        data = json.loads(attempt.data)
        assert 'akismet_status_code' not in data

        # Test that one message has been sent.
        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert attempt.title in body
        assert attempt.slug in body
        assert attempt.user.username in body

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_spam_moderator_prompt(self, mock_requests):
        rev_form = self.setup_form(mock_requests, is_spam='true')
        change_perm = Permission.objects.get(codename='change_documentspamattempt')
        self.testuser.user_permissions.add(change_perm)
        assert not rev_form.is_valid()
        assert rev_form.errors == {'__all__': [rev_form.akismet_error_message]}
        admin_path = reverse('admin:wiki_documentspamattempt_changelist')
        admin_url = admin_path + '?review__exact=0'
        assert admin_url in rev_form.akismet_error_message

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_error(self, mock_requests):
        assert DocumentSpamAttempt.objects.count() == 0
        assert len(mail.outbox) == 0
        rev_form = self.setup_form(mock_requests, is_spam='terrible')
        assert not rev_form.is_valid()
        assert rev_form.errors == {'__all__': [rev_form.akismet_error_message]}

        assert DocumentSpamAttempt.objects.count() > 0
        attempt = DocumentSpamAttempt.objects.latest()
        assert attempt.review == DocumentSpamAttempt.AKISMET_ERROR
        assert attempt.data
        data = json.loads(attempt.data)
        assert data['akismet_status_code'] == 200
        assert data['akismet_debug_help'] == 'Not provided'
        assert data['akismet_response'] == 'terrible'

        assert len(mail.outbox) == 1

    @pytest.mark.spam
    @requests_mock.mock()
    @override_switch(SPAM_TRAINING_SWITCH, True)
    def test_akismet_spam_training(self, mock_requests):
        assert not DocumentSpamAttempt.objects.exists()
        rev_form = self.setup_form(mock_requests, is_spam='true')
        assert rev_form.is_valid()
        assert DocumentSpamAttempt.objects.count() == 1
        attempt = DocumentSpamAttempt.objects.get()
        assert attempt.user == self.testuser
        assert attempt.review == DocumentSpamAttempt.NEEDS_REVIEW

    @pytest.mark.spam
    @requests_mock.mock()
    @override_switch(SPAM_TRAINING_SWITCH, True)
    def test_akismet_error_training(self, mock_requests):
        assert not DocumentSpamAttempt.objects.exists()
        rev_form = self.setup_form(mock_requests, is_spam='error')
        assert rev_form.is_valid()
        assert DocumentSpamAttempt.objects.count() == 1
        attempt = DocumentSpamAttempt.objects.get()
        assert attempt.user == self.testuser
        assert attempt.review == DocumentSpamAttempt.AKISMET_ERROR

    @pytest.mark.spam
    @requests_mock.mock()
    @override_flag(SPAM_ADMIN_FLAG, True)
    def test_akismet_parameters_admin_flag(self, mock_requests):
        rev_form = self.setup_form(mock_requests)
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert parameters['user_role'] == 'administrator'

    @pytest.mark.spam
    @requests_mock.mock()
    @override_flag(SPAM_SPAMMER_FLAG, True)
    def test_akismet_parameters_spammer_flag(self, mock_requests):
        rev_form = self.setup_form(mock_requests, is_spam='true')
        assert not rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert parameters['comment_author'] == 'viagra-test-123'

    @pytest.mark.spam
    @requests_mock.mock()
    @override_flag(SPAM_TESTING_FLAG, True)
    def test_akismet_parameters_testing_flag(self, mock_requests):
        rev_form = self.setup_form(mock_requests)
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert parameters['is_test']

    @pytest.mark.spam
    @requests_mock.mock()
    def test_akismet_set_review_flags(self, mock_requests):
        only_set_review_flags = {
            'content': self.original['content'],
            'comment': '',
            'review_tags': ['editorial', 'technical']
        }
        rev_form = self.setup_form(mock_requests,
                                   override_data=only_set_review_flags,
                                   is_spam='true')

        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert parameters['comment_content'] == ''
        assert mock_requests.call_count == 1  # Only verify key called

    @pytest.mark.spam
    @requests_mock.mock()
    def test_akismet_significant_normalized_whitespace(self, mock_requests):
        """
        Whitespace is signficant when analyzing a change.

        This can be fixed after some long-standing issues with content tidying
        are addressed.  See bug 1358541.
        """
        original = (
            '<h2 id="Summary">Tabs</h2>\r\n'
            '<p>\r\n'
            '\tThe "tab" or tabulator key, was added to typewriters in\r\n'
            '\tthe late 19th century, to aid in the typing of tabular data\r\n'
            '\tsuch as columns of numbers. In the modern computing era, a\r\n'
            '\tdomain-specific language such as CSV or HTML tables\r\n'
            '\tshould be used for tabular data. It is an on-going\r\n'
            '\teffort to remove the deprecated tab character from\r\n'
            '\tsource documents.\r\n'
            '</p>\r\n')
        new = (
            '<h2 id="Summary">Tabs</h2>\r\n'
            '<p>\r\n'
            '  The "tab" or tabulator key, was added to typewriters in\n'
            '  the late 19th century, to aid in the typing of tabular data\n'
            '  such as columns of numbers. In the modern computing era, a\n'
            '  domain-specific language such as CSV or HTML tables\n'
            '  should be used for tabular data. It is an on-going\n'
            '  effort to remove the deprecated tab character from\n'
            '  source documents.\r\n'
            '</p>\n')
        rev_form = self.setup_form(mock_requests,
                                   override_original={'content': original},
                                   override_data={'content': new})
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        # Akismet sees a content change due to the whitespace
        assert parameters['comment_content'] != ''


class RevisionFormCreateTests(RevisionFormViewTests):
    """Test RevisionForm as used in create view."""

    view_data = {  # Data passed by view, derived from POST
        'comment': 'Initial version',
        'content': (
            '<h2 id="Summary">Summary</h2>\r\n'
            '<p>Web accessibility is removing barriers that prevent'
            ' interaction with or access to website.</p>\r\n'
        ),
        'locale': 'en-US',  # Added in view from request.LANGUAGE_CODE
        'review_tags': ['technical', 'editorial'],
        'slug': 'Accessibility',
        'tags': '"Accessibility" "Web Development"',
        'title': 'Accessibility',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }

    def setup_form(self, mock_requests, is_spam='false'):
        """
        Setup a RevisionForm for a POST to create a new page.

        Parameters:
        * mock_requests - Mockable requests for Akismet checks
        """
        revision(save=True, slug='Web')
        parent = revision(save=True, slug='Web/Guide')
        data = self.view_data.copy()
        data['parent_topic'] = str(parent.id)

        request = self.rf.post('/en-US/docs/new')
        request.user = self.testuser
        # In the view, the form data's locale is set from the request
        request.LANGUAGE_CODE = data['locale']

        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content=is_spam)

        parent_slug = 'Web/Guide'
        rev_form = RevisionForm(request=request,
                                data=data,
                                parent_slug=parent_slug)
        return rev_form

    @pytest.mark.spam
    @requests_mock.mock()
    def test_standard_new(self, mock_requests):
        """Test that new English pages get the standard Akismet parameters."""
        rev_form = self.setup_form(mock_requests)
        assert rev_form.is_valid(), rev_form.errors
        parameters = rev_form.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys
        assert parameters['blog'] == 'http://testserver/'
        assert parameters['blog_charset'] == 'UTF-8'
        assert parameters['blog_lang'] == 'en_us'
        assert parameters['comment_author'] == 'Test User'
        assert parameters['comment_author_email'] == self.testuser.email
        expected_content = (
            'Accessibility\n'
            'Web/Guide/Accessibility\n'
            '<h2 id="Summary">Summary</h2>\n'
            '<p>Web accessibility is removing barriers that prevent'
            ' interaction with or access to website.</p>\n'
            'Initial version\n'
            'Accessibility\n'
            'Web Development'
        )
        assert parameters['comment_content'] == expected_content
        assert parameters['comment_type'] == 'wiki-revision'
        assert parameters['referrer'] == ''
        assert parameters['user_agent'] == ''
        assert parameters['user_ip'] == '127.0.0.1'

    @requests_mock.mock()
    @pytest.mark.spam
    def test_akismet_spam(self, mock_requests):
        assert DocumentSpamAttempt.objects.count() == 0
        assert len(mail.outbox) == 0
        rev_form = self.setup_form(mock_requests, is_spam='true')
        assert not rev_form.is_valid()
        assert rev_form.errors == {'__all__': [rev_form.akismet_error_message]}

        assert DocumentSpamAttempt.objects.count() > 0
        attempt = DocumentSpamAttempt.objects.latest()
        assert attempt.title == 'Accessibility'
        assert attempt.slug == 'Web/Guide/Accessibility'
        assert attempt.user == self.testuser
        assert attempt.review == DocumentSpamAttempt.NEEDS_REVIEW
        assert attempt.data
        data = json.loads(attempt.data)
        assert 'akismet_status_code' not in data

        # Test that one message has been sent.
        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert attempt.title in body
        assert attempt.slug in body
        assert attempt.user.username in body


class RevisionFormNewTranslationTests(RevisionFormViewTests):
    """Test RevisionForm as used to create a page in translate view."""

    original = {  # Default attributes of original English page
        'content': (
            '<h2 id="Summary">Summary</h2>\n'
            '<p><strong>HyperText Markup Language (HTML)</strong> is the'
            ' core language of nearly all Web content.</p>\n'
        ),
        'slug': 'Web/Guide/HTML',
        'tags': '"HTML" "Landing" "Web"',
        'title': 'HTML developer guide',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }

    view_data = {  # Data passed by view, derived from POST
        'comment': u'Traduction initiale',
        'content': (
            u'<h2 id="Summary">Summary</h2>\n'
            u'<p><strong>HyperText Markup Language (HTML)</strong>, ou'
            u' <em>langage de balisage hypertexte</em>, est le langage au cœur'
            u' de presque tout contenu Web.</p>\n'
        ),
        'current_rev': '',
        'form': 'both',
        'locale': 'fr',  # Added in view from request.GET to_locale
        'localization_tags': ['inprogress'],
        'slug': 'HTML',
        'tags': '"HTML" "Landing" "Web"',
        'title': u'Guide de développement HTML',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }

    def setup_form(self, mock_requests):
        """
        Setup a RevisionForm for a POST to create a new translation.

        Parameters:
        * mock_requests - Mockable requests for Akismet checks
        """
        revision(save=True, slug='Web')
        revision(save=True, slug='Web/Guide')
        original_data = self.original.copy()
        english_rev = revision(save=True, **original_data)

        fr_web_doc = document(save=True, slug='Web', locale='fr')
        revision(save=True, slug='Web', document=fr_web_doc)
        fr_guide_doc = document(save=True, slug='Web/Guide', locale='fr')
        revision(save=True, slug='Web/Guide', document=fr_guide_doc)
        fr_html_doc = document(save=True, slug='Web/Guide/HTML', locale='fr',
                               parent=english_rev.document)

        initial = {
            'based_on': english_rev.id,
            'comment': '',
            'toc_depth': english_rev.toc_depth,
            'localization_tags': ['inprogress'],
            'content': english_rev.content,  # In view, includes cleaning
        }

        request = self.rf.post('/en-US/docs/Web/Guide/HTML$translate')
        request.user = self.testuser

        is_spam = 'false'
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content=is_spam)

        parent_slug = 'Web/Guide'
        rev_form1 = RevisionForm(request=request,
                                 instance=None,
                                 initial=initial,
                                 parent_slug=parent_slug)
        assert rev_form1

        data = self.view_data.copy()
        data['based_on'] = str(english_rev.id)
        rev_form = RevisionForm(request=request,
                                data=data,
                                parent_slug=parent_slug)
        rev_form.instance.document = fr_html_doc
        return rev_form

    @pytest.mark.spam
    @requests_mock.mock()
    def test_new_translation(self, mock_requests):
        """Test Akismet dual locale setting for new translations."""
        rev_form = self.setup_form(mock_requests)
        assert rev_form.is_valid()
        parameters = rev_form.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys
        assert parameters['blog_lang'] == 'fr, en_us'
        expected_content = (
            u'Guide de développement HTML\n'
            u'<p><strong>HyperText Markup Language (HTML)</strong>, ou'
            u' <em>langage de balisage hypertexte</em>, est le langage au cœur'
            u' de presque tout contenu Web.</p>\n'
            u'Traduction initiale'
        )
        assert parameters['comment_content'] == expected_content


class RevisionFormEditTranslationTests(RevisionFormViewTests):
    """Test RevisionForm as used to create a page in translate view."""

    en_original = {  # Default attributes of original English page
        'content': (
            '<h2 id="Summary">Summary</h2>\n'
            '<p><strong>HyperText Markup Language (HTML)</strong> is the'
            ' core language of nearly all Web content.</p>\n'
        ),
        'slug': 'Web/Guide/HTML',
        'tags': '"HTML" "Landing" "Web"',
        'title': 'HTML developer guide',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }

    fr_original = {  # Default attributes of original French page
        'content': (
            u'<h2 id="Summary">Summary</h2>\n'
            u'<p><strong>HyperText Markup Language (HTML)</strong>, ou'
            u' <em>langage de balisage hypertexte</em>, est le langage au cœur'
            u' de presque tout contenu Web.</p>\n'
        ),
        'slug': 'Web/Guide/HTML',
        'tags': '"HTML" "Landing"',
        'title': u'Guide de développement HTML',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }

    view_data = {  # Data passed by view, derived from POST
        'comment': u'Traduction initiale terminée',
        'content': (
            u'<h2 id="Summary">Summary</h2>\n'
            u'<p><strong>HyperText Markup Language (HTML)</strong>, ou'
            u' <em>langage de balisage hypertexte</em>, est le langage au cœur'
            u' de presque tout contenu Web.</p>\n'
            u'<p>La majorité de ce que vous voyez dans votre navigateur est'
            u' décrit en utilisant HTML.<p>'
        ),
        'current_rev': '',
        'form': 'both',
        'locale': 'fr',  # Added in view from request.GET to_locale
        'localization_tags': ['inprogress'],
        'slug': 'HTML',
        'tags': '"HTML" "Landing" "Web"',
        'title': u'Guide de développement HTML',
        'toc_depth': Revision.TOC_DEPTH_ALL,
    }

    def setup_forms(self, mock_requests):
        """
        Setup two RevisionForms for a POST to edit an existing translation.

        RevisionForm is validated twice on POST (during Document validation,
        and during Revision validation and save), so this returns two forms

        Parameters:
        * mock_requests - Mockable requests for Akismet checks
        """
        revision(save=True, slug='Web')
        revision(save=True, slug='Web/Guide')
        en_rev = revision(save=True, **self.en_original)

        fr_web_doc = document(save=True, slug='Web', locale='fr')
        revision(save=True, slug='Web', document=fr_web_doc)
        fr_guide_doc = document(save=True, slug='Web/Guide', locale='fr')
        revision(save=True, slug='Web/Guide', document=fr_guide_doc)
        fr_html_doc = document(save=True, slug='Web/Guide/HTML', locale='fr',
                               parent=en_rev.document)
        revision(save=True, document=fr_html_doc, **self.fr_original)

        request = self.rf.post('/fr/docs/Web/Guide/HTML')
        request.user = self.testuser

        is_spam = 'false'
        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(CHECK_URL, content=is_spam)

        # Form #1 - Document validation
        data = self.view_data.copy()
        data['based_on'] = str(en_rev.id)
        data['parent_id'] = str(en_rev.document.id)
        parent_slug = 'Web/Guide'
        rev_form1 = RevisionForm(request=request,
                                 data=data,
                                 parent_slug=parent_slug)

        # Form #2 - Revision validation and saving
        data = self.view_data.copy()
        data['based_on'] = str(en_rev.id)
        data['parent_id'] = str(en_rev.document.id)
        rev_form2 = RevisionForm(request=request,
                                 data=data,
                                 parent_slug=parent_slug)
        rev_form2.instance.document = fr_html_doc

        return rev_form1, rev_form2

    @pytest.mark.spam
    @requests_mock.mock()
    def test_edit_translation(self, mock_requests):
        rev_form1, rev_form2 = self.setup_forms(mock_requests)
        assert rev_form1.is_valid(), rev_form1.errors
        assert rev_form2.is_valid(), rev_form2.errors
        parameters = rev_form2.akismet_parameters()
        assert sorted(parameters.keys()) == self.akismet_keys_edit
        assert parameters['blog_lang'] == 'fr, en_us'
        expected_content = (
            u'<p>La majorité de ce que vous voyez dans votre navigateur est'
            u' décrit en utilisant HTML.<p>\n'
            u'Traduction initiale terminée\n'
            u'Web'
        )
        assert parameters['comment_content'] == expected_content
        assert parameters['permalink'] == ('http://testserver/fr/docs/'
                                           'Web/Guide/HTML')


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
