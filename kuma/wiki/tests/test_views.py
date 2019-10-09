# -*- coding: utf-8 -*-
import datetime
import json

import mock
import pytest
import requests_mock
from constance.test import override_config
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.template.loader import render_to_string
from django.utils.six.moves import html_parser
from django.utils.six.moves.urllib.parse import parse_qs, urlencode, urlparse
from pyquery import PyQuery as pq
from waffle.testutils import override_flag, override_switch

from kuma.core.templatetags.jinja_helpers import add_utm
from kuma.core.tests import (assert_no_cache_header,
                             assert_shared_cache_header,
                             call_on_commit_immediately,
                             get_user)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import to_html
from kuma.spam.constants import (
    SPAM_CHECKS_FLAG, SPAM_SUBMISSIONS_FLAG, VERIFY_URL)
from kuma.users.tests import UserTestCase

from . import (create_document_tree, document, make_translation,
               new_document_data, normalize_html, revision, WikiTestCase)
from ..content import get_seo_description
from ..events import EditDocumentEvent, EditDocumentInTreeEvent
from ..forms import MIDAIR_COLLISION
from ..models import Document, RevisionIP
from ..templatetags.jinja_helpers import get_compare_url
from ..views.document import _get_seo_parent_title


class ViewTests(UserTestCase, WikiTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_json_view(self):
        """bug 875349"""
        expected_tags = sorted(['foo', 'bar', 'baz'])
        expected_review_tags = sorted(['tech', 'editorial'])

        doc = Document.objects.get(pk=1)
        doc.tags.set(*expected_tags)
        doc.current_revision.review_tags.set(*expected_review_tags)

        url = reverse('wiki.json')

        resp = self.client.get(url, {'title': 'an article title'})
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        data = json.loads(resp.content)
        assert data['slug'] == 'article-title'

        result_tags = sorted([str(x) for x in data['tags']])
        assert result_tags == expected_tags

        result_review_tags = sorted([str(x) for x in data['review_tags']])
        assert result_review_tags == expected_review_tags

        url = reverse('wiki.json_slug', args=('article-title',))
        with override_switch('application_ACAO', True):
            resp = self.client.get(url)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert resp['Access-Control-Allow-Origin'] == '*'
        data = json.loads(resp.content)
        assert data['title'] == 'an article title'
        assert 'translations' in data

        result_tags = sorted([str(x) for x in data['tags']])
        assert result_tags == expected_tags

        result_review_tags = sorted([str(x) for x in data['review_tags']])
        assert result_review_tags == expected_review_tags

    def test_toc_view(self):
        slug = 'toc_test_doc'
        html = '<h2>Head 2</h2><h3>Head 3</h3>'

        doc = document(title='blah', slug=slug, html=html, save=True,
                       locale=settings.WIKI_DEFAULT_LANGUAGE)
        revision(document=doc, content=html, is_approved=True, save=True)

        url = reverse('wiki.toc', args=[slug])

        with override_switch('application_ACAO', True):
            resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert resp['Access-Control-Allow-Origin'] == '*'
        assert normalize_html(resp.content) == normalize_html(
            '<ol><li><a href="#Head_2" rel="internal">Head 2</a></ol>'
        )

    @override_switch('application_ACAO', True)
    def test_children_view(self):
        """bug 875349"""
        test_content = '<p>Test <a href="http://example.com">Summary</a></p>'

        def _make_doc(title, slug, parent=None, is_redir=False):
            doc = document(title=title,
                           slug=slug,
                           save=True,
                           is_redirect=is_redir)
            if is_redir:
                content = 'REDIRECT <a class="redirect" href="/en-US/blah">Blah</a>'
            else:
                content = test_content
                revision(document=doc,
                         content=test_content,
                         summary=get_seo_description(
                             test_content,
                             strip_markup=False),
                         save=True)
            doc.html = content
            if parent:
                doc.parent_topic = parent
            doc.save()
            return doc

        root_doc = _make_doc('Root', 'Root')
        child_doc_1 = _make_doc('Child 1', 'Root/Child_1', root_doc)
        _make_doc('Grandchild 1', 'Root/Child_1/Grandchild_1', child_doc_1)
        grandchild_doc_2 = _make_doc('Grandchild 2',
                                     'Root/Child_1/Grandchild_2',
                                     child_doc_1)
        _make_doc('Great Grandchild 1',
                  'Root/Child_1/Grandchild_2/Great_Grand_Child_1',
                  grandchild_doc_2)
        _make_doc('Child 2', 'Root/Child_2', root_doc)
        _make_doc('Child 3', 'Root/Child_3', root_doc, True)

        for expand in (True, False):
            url = reverse('wiki.children', args=['Root'])
            if expand:
                url = '%s?expand' % url
            resp = self.client.get(url)
            assert resp.status_code == 200
            assert_shared_cache_header(resp)
            assert resp['Access-Control-Allow-Origin'] == '*'
            json_obj = json.loads(resp.content)

            # Basic structure creation testing
            assert json_obj['slug'] == 'Root'
            if not expand:
                assert 'summary' not in json_obj
            else:
                assert (json_obj['summary'] ==
                        'Test <a href="http://example.com">Summary</a>')
                assert 'tags' in json_obj
                assert 'review_tags' in json_obj
            assert len(json_obj['subpages']) == 2
            assert len(json_obj['subpages'][0]['subpages']) == 2
            assert (json_obj['subpages'][0]['subpages'][1]['title'] ==
                    'Grandchild 2')

        # Depth parameter testing
        def _depth_test(depth, aught):
            url = (reverse('wiki.children', args=['Root']) +
                   '?depth=' + str(depth))
            resp = self.client.get(url)
            assert resp.status_code == 200
            assert_shared_cache_header(resp)
            assert resp['Access-Control-Allow-Origin'] == '*'
            json_obj = json.loads(resp.content)
            assert (len(json_obj['subpages'][0]['subpages'][1]['subpages']) ==
                    aught)

        _depth_test(2, 0)
        _depth_test(3, 1)
        _depth_test(6, 1)

        # Sorting test
        sort_root_doc = _make_doc('Sort Root', 'Sort_Root')
        _make_doc('B Child', 'Sort_Root/B_Child', sort_root_doc)
        _make_doc('A Child', 'Sort_Root/A_Child', sort_root_doc)
        resp = self.client.get(reverse('wiki.children', args=['Sort_Root']))
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert resp['Access-Control-Allow-Origin'] == '*'
        json_obj = json.loads(resp.content)
        assert json_obj['subpages'][0]['title'] == 'A Child'

        # Test if we are serving an error json if document does not exist
        no_doc_url = reverse('wiki.children', args=['nonexistentDocument'])
        resp = self.client.get(no_doc_url)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert resp['Access-Control-Allow-Origin'] == '*'
        assert (json.loads(resp.content) ==
                {'error': 'Document does not exist.'})

        # Test error json if document is a redirect
        _make_doc('Old Name', 'Old Name', is_redir=True)
        redirect_doc_url = reverse('wiki.children', args=['Old Name'])
        resp = self.client.get(redirect_doc_url)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert resp['Access-Control-Allow-Origin'] == '*'
        assert json.loads(resp.content) == {'error': 'Document has moved.'}

    def test_summary_view(self):
        """The ?summary option should restrict document view to summary"""
        rev = revision(is_approved=True, save=True, content="""
            <p>Foo bar <a href="http://example.com">baz</a></p>
            <p>Quux xyzzy</p>
        """)
        resp = self.client.get('%s?raw&summary' %
                               rev.document.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert resp.content == b'Foo bar <a href="http://example.com">baz</a>'

    @mock.patch('waffle.flag_is_active', return_value=True)
    @mock.patch('kuma.wiki.jobs.DocumentContributorsJob.get', return_value=[
        {'id': 1, 'username': 'ringo', 'email': 'ringo@apple.co.uk'},
        {'id': 2, 'username': 'john', 'email': 'lennon@apple.co.uk'},
    ])
    def test_footer_contributors(self, get_contributors, flag_is_active):
        get_contributors.return_value = [
            {'id': 1, 'username': 'ringo', 'email': 'ringo@apple.co.uk'},
            {'id': 2, 'username': 'john', 'email': 'lennon@apple.co.uk'},
        ]
        flag_is_active.return_value = True
        rev = revision(is_approved=True, save=True, content='some content')
        resp = self.client.get(rev.document.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        page = pq(resp.content)
        contributors = (page.find(":contains('Contributors to this page')")
                            .parents('.contributors-sub'))
        # just checking if the contributor link is rendered
        assert len(contributors.find('a')) == 2

    def test_revision_view_bleached_content(self):
        """Bug 821988: Revision content should be cleaned with bleach"""
        rev = revision(is_approved=True, save=True, content="""
            <a href="#" onload=alert(3)>Hahaha</a>
            <svg><svg onload=alert(3);>
        """)
        resp = self.client.get(rev.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        ct = to_html(page.find('#wikiArticle'))
        assert '<svg>' not in ct
        assert '<a href="#">Hahaha</a>' in ct

    def test_article_revision_content(self):
        doc = document(title='Testing Article', slug='Article', save=True)
        r = revision(save=True, document=doc, is_approved=True)

        resp = self.client.get(r.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)

        assert b'Revision Source' in resp.content
        assert b'Revision Content' in resp.content
        assert 'open' == page.find('#wikiArticle').parent().attr('open')
        assert page.find('#doc-source').parent().attr('open') is None


class ReadOnlyTests(UserTestCase, WikiTestCase):
    """Tests readonly scenarios"""
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def setUp(self):
        super(ReadOnlyTests, self).setUp()
        rev = revision(is_approved=True, save=True)
        self.edit_url = reverse('wiki.edit', args=[rev.document.slug])

    def test_everyone(self):
        """ kumaediting: everyone, kumabanned: none  """
        self.kumaediting_flag.everyone = True
        self.kumaediting_flag.save()

        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.edit_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

    def test_superusers_only(self):
        """ kumaediting: superusers, kumabanned: none """
        self.kumaediting_flag.everyone = None
        self.kumaediting_flag.superusers = True
        self.kumaediting_flag.save()

        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.edit_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 403
        assert b'The wiki is in read-only mode.' in resp.content
        assert_no_cache_header(resp)
        self.client.logout()

        self.client.login(username='admin', password='testpass')
        resp = self.client.get(self.edit_url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)


class KumascriptIntegrationTests(UserTestCase, WikiTestCase):
    """
    Tests for usage of the kumascript service.

    Note that these tests really just check whether or not the service was
    used, and are not integration tests meant to exercise the real service.
    """

    def setUp(self):
        super(KumascriptIntegrationTests, self).setUp()
        self.rev = revision(is_approved=True, save=True, content="TEST CONTENT")
        self.doc = self.rev.document
        self.doc.tags.set('foo', 'bar', 'baz')
        self.url = self.doc.get_absolute_url()

        # TODO: upgrade mock to 0.8.0 so we can do this.

        # self.mock_kumascript_get = (
        #         mock.patch('kuma.wiki.kumascript.get'))
        # self.mock_kumascript_get.return_value = self.doc.html

    def tearDown(self):
        super(KumascriptIntegrationTests, self).tearDown()

        # TODO: upgrade mock to 0.8.0 so we can do this.

        # self.mock_kumascript_get.stop()

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_basic_view(self, mock_kumascript_get):
        """When kumascript timeout is non-zero, the service should be used"""
        mock_kumascript_get.return_value = (self.doc.html, None)
        self.client.get(self.url, follow=False, HTTP_HOST=settings.WIKI_HOST)
        assert mock_kumascript_get.called, "kumascript should have been used"

    @override_config(KUMASCRIPT_TIMEOUT=0.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_disabled(self, mock_kumascript_get):
        """When disabled, the kumascript service should not be used"""
        mock_kumascript_get.return_value = (self.doc.html, None)
        self.client.get(self.url, follow=False, HTTP_HOST=settings.WIKI_HOST)
        assert not mock_kumascript_get.called, "kumascript should not have been used"

    @override_config(KUMASCRIPT_TIMEOUT=0.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_disabled_rendering(self, mock_kumascript_get):
        """When disabled, the kumascript service should not be used
        in rendering"""
        mock_kumascript_get.return_value = (self.doc.html, None)
        self.doc.schedule_rendering('max-age=0')
        assert not mock_kumascript_get.called, "kumascript should not have been used"

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_nomacros(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.doc.html, None)
        self.client.get('%s?nomacros' % self.url, follow=False,
                        HTTP_HOST=settings.WIKI_HOST)
        assert not mock_kumascript_get.called, "kumascript should not have been used"

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_raw(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.doc.html, None)
        self.client.get('%s?raw' % self.url, follow=False,
                        HTTP_HOST=settings.WIKI_HOST)
        assert not mock_kumascript_get.called, "kumascript should not have been used"

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_raw_macros(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.doc.html, None)
        self.client.get('%s?raw&macros' % self.url, follow=False,
                        HTTP_HOST=settings.WIKI_HOST)
        assert mock_kumascript_get.called, "kumascript should have been used"

    @override_config(KUMASCRIPT_TIMEOUT=1.0, KUMASCRIPT_MAX_AGE=600)
    @requests_mock.mock()
    def test_preview_nonascii(self, mock_requests):
        """POSTing non-ascii to kumascript should encode to utf8"""
        content = u'Français'
        mock_requests.post(requests_mock.ANY, content=content.encode('utf8'))

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(reverse('wiki.preview'), {'content': content},
                                HTTP_HOST=settings.WIKI_HOST)
        assert_no_cache_header(resp)
        # No UnicodeDecodeError
        mock_requests.request_history[0].body.decode('utf8')

    @override_config(KUMASCRIPT_TIMEOUT=1.0, KUMASCRIPT_MAX_AGE=600)
    @mock.patch('kuma.wiki.kumascript.post')
    def test_dont_render_previews_for_deferred_docs(self, mock_post):
        """
        When a user previews a document with deferred rendering,
        we want to force the preview to skip the kumascript POST,
        so that big previews can't use up too many kumascript connections.

        bug 1197971
        """
        self.doc.defer_rendering = True
        self.doc.save()
        mock_post.side_effect = Exception("Should not be called")

        self.client.login(username='admin', password='testpass')
        resp = self.client.post(reverse('wiki.preview'),
                                {'doc_id': self.doc.id},
                                HTTP_HOST=settings.WIKI_HOST)
        assert_no_cache_header(resp)


class DocumentSEOTests(UserTestCase, WikiTestCase):
    """Tests for the document seo logic"""

    def test_get_seo_parent_doesnt_throw_404(self):
        """bug 1190212"""
        doc = document(save=True)
        slug_dict = {'seo_root': 'Root/Does/Not/Exist'}
        _get_seo_parent_title(doc, slug_dict, 'bn')  # Should not raise Http404

    def test_seo_title(self):
        self.client.login(username='admin', password='testpass')

        # Utility to make a quick doc
        def _make_doc(title, aught_titles, slug):
            doc = document(save=True, slug=slug, title=title,
                           locale=settings.WIKI_DEFAULT_LANGUAGE)
            revision(save=True, document=doc)
            response = self.client.get(reverse('wiki.document', args=[slug]),
                                       HTTP_HOST=settings.WIKI_HOST)
            page = pq(response.content)

            assert page.find('head > title').text() in aught_titles

        # Test nested document titles
        _make_doc('One', ['One | MDN'], 'one')
        _make_doc('Two', ['Two - One | MDN'], 'one/two')
        _make_doc('Three', ['Three - One | MDN'], 'one/two/three')
        _make_doc(u'Special Φ Char',
                  [u'Special \u03a6 Char - One | MDN',
                   u'Special \xce\xa6 Char - One | MDN'],
                  'one/two/special_char')

        # Additional tests for /Web/*  changes
        _make_doc('Firefox OS', ['Firefox OS | MDN'], 'firefox_os')
        _make_doc('Email App', ['Email App - Firefox OS | MDN'],
                  'firefox_os/email_app')
        _make_doc('Web', ['Web | MDN'], 'Web')
        _make_doc('HTML', ['HTML | MDN'], 'Web/html')
        _make_doc('Fieldset', ['Fieldset - HTML | MDN'], 'Web/html/fieldset')
        _make_doc('Legend', ['Legend - HTML | MDN'],
                  'Web/html/fieldset/legend')

    def test_seo_script(self):
        self.client.login(username='admin', password='testpass')

        def make_page_and_compare_seo(slug, content, aught_preview):
            # Create the doc
            data = new_document_data()
            data.update({'title': 'blah', 'slug': slug, 'content': content})
            response = self.client.post(reverse('wiki.create'), data,
                                        HTTP_HOST=settings.WIKI_HOST)
            assert 302 == response.status_code

            # Connect to newly created page
            response = self.client.get(reverse('wiki.document', args=[slug]),
                                       HTTP_HOST=settings.WIKI_HOST)
            page = pq(response.content)
            meta_content = page.find('meta[name=description]').attr('content')
            assert str(meta_content) == str(aught_preview)

        # Test pages - very basic
        good = 'This is the content which should be chosen, man.'
        make_page_and_compare_seo('one', '<p>' + good + '</p>', good)
        # No content, no seo
        make_page_and_compare_seo('two', 'blahblahblahblah<br />', None)
        # No summary, no seo
        make_page_and_compare_seo('three', '<div><p>You cant see me</p></div>',
                                  None)
        # Warning paragraph ignored
        make_page_and_compare_seo('four',
                                  '<div class="geckoVersion">'
                                  '<p>No no no</p></div><p>yes yes yes</p>',
                                  'yes yes yes')
        # Warning paragraph ignored, first one chosen if multiple matches
        make_page_and_compare_seo('five',
                                  '<div class="geckoVersion"><p>No no no</p>'
                                  '</div><p>yes yes yes</p>'
                                  '<p>ignore ignore ignore</p>',
                                  'yes yes yes')
        # Don't take legacy crumbs
        make_page_and_compare_seo('six', u'<p>« CSS</p><p>I am me!</p>',
                                  'I am me!')
        # Take the seoSummary class'd element
        make_page_and_compare_seo('seven',
                                  u'<p>I could be taken</p>'
                                  '<p class="seoSummary">I should be though</p>',
                                  'I should be though')
        # Two summaries append
        make_page_and_compare_seo('eight',
                                  u'<p>I could be taken</p>'
                                  '<p class="seoSummary">a</p>'
                                  '<p class="seoSummary">b</p>',
                                  'a b')

        # No brackets
        make_page_and_compare_seo('nine',
                                  u'<p>I <em>am</em> awesome.'
                                  ' <a href="blah">A link</a> is also &lt;cool&gt;</p>',
                                  u'I am awesome. A link is also cool')


@pytest.mark.parametrize('content,expected', [
    ('<div onclick="alert(\'hacked!\')">click me</div>',
     '<div>click me</div>'),
    ('<svg><circle onload=confirm(3)>',
     '&lt;svg&gt;&lt;circle onload="confirm(3)"&gt;&lt;/circle&gt;&lt;/svg&gt;')
], ids=('strip', 'escape'))
def test_editor_safety(root_doc, editor_client, content, expected):
    """
    When editing or translating, the content should already have been
    bleached, so for example, any harmful on* attributes stripped or
    escaped (see bug 821986).
    """
    rev = root_doc.current_revision
    rev.content = content
    rev.save()
    args = (root_doc.slug,)
    urls = (
        reverse('wiki.edit', args=args),
        '%s?tolocale=%s' % (reverse('wiki.translate', args=args), 'fr')
    )
    for url in urls:
        response = editor_client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        page = pq(response.content)
        editor_src = page.find('#id_content').text()
        assert editor_src == expected


class DocumentEditingTests(UserTestCase, WikiTestCase):
    """Tests for the document-editing view"""

    def test_create_on_404(self):
        self.client.login(username='admin', password='testpass')

        # Create the parent page.
        rev = revision(is_approved=True, save=True)

        # Establish attribs of child page.
        local_slug = 'Some_New_Title'
        slug = '%s/%s' % (rev.document.slug, local_slug)
        url = reverse('wiki.document', args=[slug])

        # Ensure redirect to create new page on attempt to visit non-existent
        # child page.
        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)
        assert 'public' not in resp['Cache-Control']
        assert 's-maxage' not in resp['Cache-Control']
        assert 'docs/new' in resp['Location']
        assert ('slug=%s' % local_slug) in resp['Location']

        # Ensure real 404 for visit to non-existent page with params common to
        # kumascript and raw content API.
        for p_name in ('raw', 'include', 'nocreate'):
            sub_url = '%s?%s=1' % (url, p_name)
            resp = self.client.get(sub_url, HTTP_HOST=settings.WIKI_HOST)
            assert resp.status_code == 404

        # Ensure root level documents work, not just children
        response = self.client.get(reverse('wiki.document', args=['noExist']),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert 'public' not in response['Cache-Control']
        assert 'no-cache' in resp['Cache-Control']
        assert 'docs/new' in response['Location']

        response = self.client.get(reverse('wiki.document',
                                           args=['Template:NoExist']),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert 'public' not in response['Cache-Control']
        assert 'no-cache' in resp['Cache-Control']
        assert 'docs/new' in response['Location']

    def test_creating_child_of_redirect(self):
        """
        While try to create a child of a redirect,
        the parent of the child should be redirect's parent.
        """
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True)
        doc = rev.document
        doc_first_slug = doc.slug
        # Move the document to new slug
        doc._move_tree(new_slug="moved_doc")

        # Try to create a child with the old slug
        child_full_slug = doc_first_slug + "/" + "children_document"
        url = reverse('wiki.document', args=[child_full_slug])
        response = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert 'public' not in response['Cache-Control']
        assert 'no-cache' in response['Cache-Control']
        assert 'docs/new' in response['Location']
        # The parent id of the query should be same because while moving,
        # a new document is created with old slug and make redirect to the
        # old document
        parameters = parse_qs(urlparse(response['Location']).query)
        assert parameters['parent'][0] == str(doc.id)

    def test_child_of_redirect_to_non_document(self):
        """Return a 404 when accessing the child of a non-document redirect."""
        self.client.login(username='admin', password='testpass')
        content = '<p>REDIRECT <a class="redirect" href="/">MDN</a></p>'
        rev = revision(content=content, is_approved=True, save=True)
        doc = rev.document
        assert doc.is_redirect
        assert doc.get_redirect_url() == '/'
        assert doc.get_redirect_document() is None

        doc_url = doc.get_absolute_url()
        response = self.client.get(doc_url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 301
        assert response['Location'] == '/'

        subpage_url = doc_url + '/SubPage'
        response = self.client.get(subpage_url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 404

    @pytest.mark.retitle
    def test_retitling_solo_doc(self):
        """ Editing just title of non-parent doc:
            * Changes title
            * Doesn't cause errors
            * Doesn't create redirect
        """
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        self.client.login(username='admin', password='testpass')

        new_title = 'Some New Title'
        rev = revision(is_approved=True, save=True)
        doc = rev.document

        old_title = doc.title
        data = new_document_data()
        data.update({'title': new_title,
                     'form-type': 'rev'})
        data['slug'] = ''
        url = reverse('wiki.edit', args=[doc.slug])
        response = self.client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert (Document.objects.get(slug=doc.slug, locale=doc.locale).title ==
                new_title)
        assert not Document.objects.filter(title=old_title).exists()

    @pytest.mark.retitle
    def test_retitling_parent_doc(self):
        """ Editing just title of parent doc:
            * Changes title
            * Doesn't cause errors
            * Doesn't create redirect
        """
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        self.client.login(username='admin', password='testpass')

        # create parent doc & rev along with child doc & rev
        d = document(title='parent', save=True)
        revision(document=d, content='parent', save=True)
        d2 = document(title='child', parent_topic=d, save=True)
        revision(document=d2, content='child', save=True)

        old_title = d.title
        new_title = 'Some New Title'
        data = new_document_data()
        data.update({'title': new_title,
                     'form-type': 'rev'})
        data['slug'] = ''
        url = reverse('wiki.edit', args=[d.slug])
        response = self.client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert (Document.objects.get(slug=d.slug, locale=d.locale).title ==
                new_title)
        assert not Document.objects.filter(title=old_title).exists()

    def test_slug_change_ignored_for_iframe(self):
        """When the title of an article is edited in an iframe, the change is
        ignored."""
        self.client.login(username='admin', password='testpass')
        new_slug = 'some_new_slug'
        rev = revision(is_approved=True, save=True)
        old_slug = rev.document.slug
        data = new_document_data()
        data.update({'title': rev.document.title,
                     'slug': new_slug,
                     'form': 'rev'})
        response = self.client.post('%s?iframe=1' %
                                    reverse('wiki.edit',
                                            args=[rev.document.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert (Document.objects.get(slug=rev.document.slug,
                                     locale=rev.document.locale).slug ==
                old_slug)
        assert "REDIRECT" not in Document.objects.get(slug=old_slug).html

    @pytest.mark.clobber
    def test_slug_collision_errors(self):
        """When an attempt is made to retitle an article and another with that
        title already exists, there should be form errors"""
        self.client.login(username='admin', password='testpass')

        exist_slug = "existing-doc"

        # Create a new doc.
        data = new_document_data()
        data.update({"slug": exist_slug})
        resp = self.client.post(reverse('wiki.create'), data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302

        # Create another new doc.
        data = new_document_data()
        data.update({"slug": 'some-new-title'})
        resp = self.client.post(reverse('wiki.create'), data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302

        # Now, post an update with duplicate slug
        data.update({
            'form-type': 'rev',
            'slug': exist_slug
        })
        resp = self.client.post(reverse('wiki.edit', args=['some-new-title']),
                                data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        p = pq(resp.content)
        assert p.find('.errorlist').length > 0
        assert p.find('.errorlist a[href="#id_slug"]').length > 0

    @pytest.mark.clobber
    def test_redirect_can_be_clobbered(self):
        """When an attempt is made to retitle an article, and another article
        with that title exists but is a redirect, there should be no errors and
        the redirect should be replaced."""
        self.client.login(username='admin', password='testpass')

        exist_title = "Existing doc"
        exist_slug = "existing-doc"

        changed_title = 'Changed title'
        changed_slug = 'changed-title'

        # Create a new doc.
        data = new_document_data()
        data.update({"title": exist_title, "slug": exist_slug})
        resp = self.client.post(reverse('wiki.create'), data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302

        # Change title and slug
        data.update({'form-type': 'rev',
                     'title': changed_title,
                     'slug': changed_slug})
        resp = self.client.post(reverse('wiki.edit', args=[exist_slug]),
                                data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

        # Change title and slug back to originals, clobbering the redirect
        data.update({'form-type': 'rev',
                     'title': exist_title,
                     'slug': exist_slug})
        resp = self.client.post(reverse('wiki.edit', args=[changed_slug]),
                                data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302

    def test_slug_revamp(self):
        self.client.login(username='admin', password='testpass')

        # Test that slugs with the same "specific" slug but in different levels
        # in the heiharachy are validated properly upon submission.

        # Create base doc
        parent_doc = document(title='Length',
                              slug='length',
                              is_localizable=True,
                              locale=settings.WIKI_DEFAULT_LANGUAGE)
        parent_doc.save()
        r = revision(document=parent_doc)
        r.save()

        # Create child, try to use same slug, should work
        child_data = new_document_data()
        child_data['title'] = 'Child Length'
        child_data['slug'] = 'length'
        child_data['content'] = 'This is the content'
        child_data['is_localizable'] = True
        child_url = (reverse('wiki.create') +
                     '?parent=' +
                     str(parent_doc.id))
        response = self.client.post(child_url, child_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        # grab new revision ID
        child = Document.objects.get(locale='en-US', slug='length/length')
        rev_id = child.current_revision.id
        self.assertRedirects(response,
                             reverse('wiki.document', args=['length/length']))

        # Editing newly created child "length/length" doesn't cause errors
        child_data['form-type'] = 'rev'
        child_data['slug'] = ''
        edit_url = reverse('wiki.edit', args=['length/length'])
        response = self.client.post(edit_url, child_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        url = reverse('wiki.document', args=['length/length'])
        params = {'rev_saved': rev_id}
        url = '%s?%s' % (url, urlencode(params))
        self.assertRedirects(response, url)

        # Creating a new translation of parent and child
        # named "length" and "length/length" respectively
        # doesn't cause errors
        child_data['form-type'] = 'both'
        child_data['slug'] = 'length'
        translate_url = reverse('wiki.document', args=[child_data['slug']])
        response = self.client.post(translate_url + '$translate?tolocale=es',
                                    child_data, HTTP_HOST=settings.WIKI_HOST)
        assert 302 == response.status_code
        url = reverse('wiki.document', args=[child_data['slug']], locale='es')
        params = {'rev_saved': ''}
        url = '%s?%s' % (url, urlencode(params))
        assert response['Location'] == url

        translate_url = reverse('wiki.document', args=['length/length'])
        response = self.client.post(translate_url + '$translate?tolocale=es',
                                    child_data, HTTP_HOST=settings.WIKI_HOST)
        assert 302 == response.status_code
        slug = 'length/' + child_data['slug']
        url = reverse('wiki.document', args=[slug], locale='es')
        params = {'rev_saved': ''}
        url = '%s?%s' % (url, urlencode(params))
        assert response['Location'] == url

    def test_translate_keeps_topical_parent(self):
        self.client.login(username='admin', password='testpass')
        en_doc, de_doc = make_translation()

        en_child_doc = document(parent_topic=en_doc, slug='en-child',
                                save=True)
        en_child_rev = revision(document=en_child_doc, save=True)
        de_child_doc = document(parent_topic=de_doc, locale='de',
                                slug='de-child', parent=en_child_doc,
                                save=True)
        revision(document=de_child_doc, save=True)

        post_data = {}
        post_data['slug'] = de_child_doc.slug
        post_data['title'] = 'New title'
        post_data['form'] = 'both'
        post_data['content'] = 'New translation'
        post_data['tolocale'] = 'de'
        post_data['toc_depth'] = 0
        post_data['based_on'] = en_child_rev.id
        post_data['parent_id'] = en_child_doc.id

        translate_url = reverse('wiki.edit',
                                args=[de_child_doc.slug],
                                locale='de')
        response = self.client.post(translate_url, post_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)

        de_child_doc = Document.objects.get(locale='de', slug='de-child')
        assert en_child_doc == de_child_doc.parent
        assert de_doc == de_child_doc.parent_topic
        assert 'New translation' == de_child_doc.current_revision.content

    def test_translate_keeps_toc_depth(self):
        self.client.login(username='admin', password='testpass')

        locale = settings.WIKI_DEFAULT_LANGUAGE
        original_slug = 'eng-doc'
        foreign_locale = 'es'
        foreign_slug = 'es-doc'

        en_doc = document(title='Eng Doc', slug=original_slug,
                          is_localizable=True, locale=locale)
        en_doc.save()
        r = revision(document=en_doc, toc_depth=1)
        r.save()

        post_data = new_document_data()
        post_data['title'] = 'ES Doc'
        post_data['slug'] = foreign_slug
        post_data['content'] = 'This is the content'
        post_data['is_localizable'] = True
        post_data['form'] = 'both'
        post_data['toc_depth'] = r.toc_depth
        translate_url = reverse('wiki.document', args=[original_slug])
        translate_url += '$translate?tolocale=' + foreign_locale
        response = self.client.post(translate_url, post_data,
                                    HTTP_HOST=settings.WIKI_HOST)

        doc_url = reverse('wiki.document', args=[foreign_slug], locale=foreign_locale)
        params = {'rev_saved': ''}
        doc_url = '%s?%s' % (doc_url, urlencode(params))
        assert response['Location'] == doc_url

        es_d = Document.objects.get(locale=foreign_locale, slug=foreign_slug)
        assert r.toc_depth == es_d.current_revision.toc_depth

    def test_translate_rebuilds_source_json(self):
        self.client.login(username='admin', password='testpass')
        # Create an English original and a Spanish translation.
        en_slug = 'en-doc'
        es_locale = 'es'
        es_slug = 'es-doc'
        en_doc = document(title='EN Doc',
                          slug=en_slug,
                          is_localizable=True)
        en_doc.save()
        en_doc.render()

        en_doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                      slug=en_slug)
        json.loads(en_doc.json)

        r = revision(document=en_doc)
        r.save()
        translation_data = new_document_data()
        translation_data['title'] = 'ES Doc'
        translation_data['slug'] = es_slug
        translation_data['content'] = 'This is the content'
        translation_data['is_localizable'] = False
        translation_data['form'] = 'both'
        translate_url = reverse('wiki.document', args=[en_slug])
        translate_url += '$translate?tolocale=' + es_locale
        response = self.client.post(translate_url, translation_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        # Sanity to make sure the translate succeeded.
        doc_url = reverse('wiki.document', args=[es_slug], locale=es_locale)
        params = {'rev_saved': ''}
        doc_url = '%s?%s' % (doc_url, urlencode(params))
        assert response['Location'] == doc_url
        es_doc = Document.objects.get(locale=es_locale,
                                      slug=es_slug)
        es_doc.render()

        new_en_json = json.loads(Document.objects.get(pk=en_doc.pk).json)

        assert 'translations' in new_en_json
        assert (translation_data['title'] in
                [t['title'] for t in new_en_json['translations']])
        es_translation_json = [t for t in new_en_json['translations'] if
                               t['title'] == translation_data['title']][0]
        assert (es_translation_json['last_edit'] ==
                es_doc.current_revision.created.isoformat())

    def test_slug_translate(self):
        """Editing a translated doc keeps the correct slug"""
        self.client.login(username='admin', password='testpass')

        # Settings
        original_slug = 'eng-doc'
        child_slug = 'child-eng-doc'
        foreign_locale = 'es'
        foreign_slug = 'es-doc'
        foreign_child_slug = 'child-es-doc'

        # Create the one-level English Doc
        en_doc = document(title='Eng Doc',
                          slug=original_slug,
                          is_localizable=True)
        en_doc.save()
        r = revision(document=en_doc)
        r.save()

        # Translate to ES
        parent_data = new_document_data()
        parent_data['title'] = 'ES Doc'
        parent_data['slug'] = foreign_slug
        parent_data['content'] = 'This is the content'
        parent_data['is_localizable'] = True
        parent_data['form'] = 'both'
        translate_url = reverse('wiki.document', args=[original_slug])
        translate_url += '$translate?tolocale=' + foreign_locale
        response = self.client.post(translate_url, parent_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        doc_url = reverse('wiki.document', args=[foreign_slug], locale=foreign_locale)
        params = {'rev_saved': ''}
        doc_url = '%s?%s' % (doc_url, urlencode(params))
        assert response['Location'] == doc_url

        # Go to edit the translation, ensure the the slug is correct
        response = self.client.get(reverse('wiki.edit',
                                           args=[foreign_slug],
                                           locale=foreign_locale),
                                   HTTP_HOST=settings.WIKI_HOST)
        page = pq(response.content)
        assert page.find('input[name=slug]')[0].value == foreign_slug

        # Create an English child now
        en_doc = document(title='Child Eng Doc',
                          slug=original_slug + '/' + child_slug,
                          is_localizable=True,
                          locale=settings.WIKI_DEFAULT_LANGUAGE,
                          parent_topic=en_doc)
        en_doc.save()
        r = revision(document=en_doc)
        r.save()

        # Translate to ES
        child_data = new_document_data()
        child_data['title'] = 'ES Child Doc'
        child_data['slug'] = foreign_child_slug
        child_data['content'] = 'This is the content'
        child_data['is_localizable'] = True
        child_data['form'] = 'both'

        translate_url = reverse('wiki.document',
                                args=[original_slug + '/' + child_slug])
        translate_url += '$translate?tolocale=' + foreign_locale
        response = self.client.post(translate_url, child_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        slug = foreign_slug + '/' + child_data['slug']
        doc_url = reverse('wiki.document', args=[slug], locale=foreign_locale)
        params = {'rev_saved': ''}
        doc_url = '%s?%s' % (doc_url, urlencode(params))
        assert response['Location'] == doc_url

    def test_restore_translation_source(self):
        """Edit a localized article without an English parent allows user to
        set translation parent."""
        # Create english doc
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        self.client.post(reverse('wiki.create'), data,
                         HTTP_HOST=settings.WIKI_HOST)
        en_d = Document.objects.get(locale=data['locale'], slug=data['slug'])

        # Create french doc
        data.update({'locale': 'fr',
                     'title': 'A Tést Articlé',
                     'content': "C'ést bon."})
        self.client.post(reverse('wiki.create', locale='fr'), data,
                         HTTP_HOST=settings.WIKI_HOST)
        fr_d = Document.objects.get(locale=data['locale'], slug=data['slug'])

        # Check edit doc page for choose parent box
        url = reverse('wiki.edit', args=[fr_d.slug], locale='fr')
        response = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert pq(response.content)('li.metadata-choose-parent')

        # Set the parent
        data.update({'form-type': 'rev', 'parent_id': en_d.id})
        resp = self.client.post(url, data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        assert 'fr/docs/a-test-article' in resp['Location']

        # Check the languages drop-down
        resp = self.client.get(resp['Location'], HTTP_HOST=settings.WIKI_HOST)
        translations = pq(resp.content)('ul#translations li')
        assert 'English (US)' in translations.text()

    def test_translation_source(self):
        """Allow users to change "translation source" settings"""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        self.client.post(reverse('wiki.create'), data,
                         HTTP_HOST=settings.WIKI_HOST)
        parent = Document.objects.get(locale=data['locale'], slug=data['slug'])

        data.update({'title': 'Another Test Article',
                     'content': "Yahoooo!",
                     'parent_id': parent.id})
        self.client.post(reverse('wiki.create'), data,
                         HTTP_HOST=settings.WIKI_HOST)
        child = Document.objects.get(locale=data['locale'], slug=data['slug'])

        url = reverse('wiki.edit', args=[child.slug])
        response = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        content = pq(response.content)
        assert content('li.metadata-choose-parent')
        assert str(parent.id) in to_html(content)

    @pytest.mark.tags
    def test_tags_while_document_update(self):
        self.client.login(username='admin', password='testpass')
        ts1 = ('JavaScript', 'AJAX', 'DOM')
        ts2 = ('XML', 'JSON')
        # Create a revision with some tags
        rev = revision(save=True, tags=','.join(ts1))
        doc = rev.document

        # Update the document with some other tags
        data = new_document_data()
        data.update({'form-type': 'rev', 'tags': ', '.join(ts2)})
        response = self.client.post(reverse('wiki.edit', args=[doc.slug]), data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)

        # Check only last added tags are related with the documents
        doc_tags = doc.tags.all().values_list('name', flat=True)
        assert sorted(doc_tags) == sorted(ts2)

    @pytest.mark.tags
    def test_tags_showing_correctly_after_doc_update(self):
        """After any update to the document, the new tags should show correctly"""
        self.client.login(username='admin', password='testpass')
        ts1 = ('JavaScript', 'AJAX', 'DOM')
        ts2 = ('XML', 'JSON')
        rev = revision(save=True, tags=','.join(ts1))
        doc = rev.document

        # Update the document with some other tags
        data = new_document_data()
        del data['slug']
        data.update({'form-type': 'rev', 'tags': ', '.join(ts2)})
        response = self.client.post(reverse('wiki.edit', args=[doc.slug]), data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)

        # Check document is showing the new tags
        response = self.client.get(doc.get_absolute_url(), follow=True,
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200

        page = pq(response.content)
        response_tags = page.find('.tags li a').contents()
        assert response_tags == sorted(ts2)

    @pytest.mark.review_tags
    @mock.patch.object(Site.objects, 'get_current')
    def test_review_tags(self, get_current):
        """Review tags can be managed on document revisions"""
        get_current.return_value.domain = 'su.mo.com'
        self.client.login(username='admin', password='testpass')

        # Create a new doc with one review tag
        data = new_document_data()
        data.update({'review_tags': ['technical']})
        response = self.client.post(reverse('wiki.create'), data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302

        # Ensure there's now a doc with that expected tag in its newest
        # revision
        doc = Document.objects.get(slug="a-test-article")
        rev = doc.revisions.order_by('-id').all()[0]
        review_tags = [x.name for x in rev.review_tags.all()]
        assert review_tags == ['technical']

        # Now, post an update with two tags
        data.update({
            'form-type': 'rev',
            'review_tags': ['editorial', 'technical'],
        })
        response = self.client.post(reverse('wiki.edit', args=[doc.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert_no_cache_header(response)

        # Ensure the doc's newest revision has both tags.
        doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                   slug="a-test-article")
        rev = doc.revisions.order_by('-id').all()[0]
        review_tags = [x.name for x in rev.review_tags.all()]
        review_tags.sort()
        assert review_tags == ['editorial', 'technical']

        # Now, ensure that review form appears for the review tags.
        response = self.client.get(reverse('wiki.document', args=[doc.slug]),
                                   data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        page = pq(response.content)
        assert page.find('.page-meta.reviews').length == 1
        assert page.find('#id_request_technical').length == 1
        assert page.find('#id_request_editorial').length == 1

        doc_entry = '<entry><title>{}</title>'.format(doc.title)
        doc_selector = "ul.document-list li a:contains('{}')".format(doc.title)

        # Ensure the page appears on the listing pages
        response = self.client.get(reverse('wiki.list_review'),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert pq(response.content).find(doc_selector).length == 1
        response = self.client.get(reverse('wiki.list_review_tag',
                                           args=('technical',)),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert pq(response.content).find(doc_selector).length == 1
        response = self.client.get(reverse('wiki.list_review_tag',
                                           args=('editorial',)),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert pq(response.content).find(doc_selector).length == 1

        # Also, ensure that the page appears in the proper feeds
        # HACK: Too lazy to parse the XML. Lazy lazy.
        response = self.client.get(reverse('wiki.feeds.list_review',
                                           args=('atom',)),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert doc_entry.encode('utf-8') in response.content
        response = self.client.get(reverse('wiki.feeds.list_review_tag',
                                           args=('atom', 'technical', )),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert doc_entry.encode('utf-8') in response.content
        response = self.client.get(reverse('wiki.feeds.list_review_tag',
                                           args=('atom', 'editorial', )),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert doc_entry.encode('utf-8') in response.content

        # Post an edit that removes the technical review tag.
        data.update({
            'form-type': 'rev',
            'review_tags': ['editorial', ]
        })
        response = self.client.post(reverse('wiki.edit', args=[doc.slug]), data,
                                    HTTP_HOST=settings.WIKI_HOST)

        # Ensure only one of the tags' warning boxes appears, now.
        response = self.client.get(reverse('wiki.document', args=[doc.slug]),
                                   data, HTTP_HOST=settings.WIKI_HOST)
        page = pq(response.content)
        assert page.find('.page-meta.reviews').length == 1
        assert page.find('#id_request_technical').length == 0
        assert page.find('#id_request_editorial').length == 1

        # Ensure the page appears on the listing pages
        response = self.client.get(reverse('wiki.list_review'),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert pq(response.content).find(doc_selector).length == 1
        response = self.client.get(reverse('wiki.list_review_tag',
                                           args=('technical',)),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert pq(response.content).find(doc_selector).length == 0
        response = self.client.get(reverse('wiki.list_review_tag',
                                           args=('editorial',)),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        assert pq(response.content).find(doc_selector).length == 1

        # Also, ensure that the page appears in the proper feeds
        # HACK: Too lazy to parse the XML. Lazy lazy.
        response = self.client.get(reverse('wiki.feeds.list_review',
                                           args=('atom',)),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert doc_entry in response.content
        response = self.client.get(reverse('wiki.feeds.list_review_tag',
                                           args=('atom', 'technical', )),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert doc_entry not in response.content
        response = self.client.get(reverse('wiki.feeds.list_review_tag',
                                           args=('atom', 'editorial', )),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert doc_entry in response.content

    @pytest.mark.review_tags
    def test_quick_review(self):
        """Test the quick-review button."""
        self.client.login(username='admin', password='testpass')

        test_data = [
            {
                'params': {'request_technical': 1},
                'expected_tags': ['technical'],
                'name': 'technical',
                'message_contains': [
                    'Editorial review completed.',
                ]
            },
            {
                'params': {'request_editorial': 1},
                'expected_tags': ['editorial'],
                'name': 'editorial',
                'message_contains': [
                    'Technical review completed.',
                ]
            },
            {
                'params': {},
                'expected_tags': [],
                'name': 'editorial-technical',
                'message_contains': [
                    'Technical review completed.',
                    'Editorial review completed.',
                ]
            }
        ]

        for data_dict in test_data:
            slug = 'test-quick-review-%s' % data_dict['name']
            data = new_document_data()
            data.update({'review_tags': ['editorial', 'technical'], 'slug': slug})
            resp = self.client.post(reverse('wiki.create'), data,
                                    HTTP_HOST=settings.WIKI_HOST)

            doc = Document.objects.get(slug=slug)
            rev = doc.revisions.order_by('-id').all()[0]
            review_url = reverse('wiki.quick_review',
                                 args=[doc.slug])

            params = dict(data_dict['params'], revision_id=rev.id)
            resp = self.client.post(review_url, params,
                                    HTTP_HOST=settings.WIKI_HOST)
            assert resp.status_code == 302
            assert_no_cache_header(resp)
            doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                       slug=slug)
            rev = doc.revisions.order_by('-id').all()[0]
            review_tags = [x.name for x in rev.review_tags.all()]
            review_tags.sort()
            for expected_str in data_dict['message_contains']:
                assert expected_str in rev.summary
                assert expected_str in rev.comment
            assert review_tags == data_dict['expected_tags']

    @pytest.mark.midair
    def test_edit_midair_collisions(self, is_ajax=False, translate_locale=None):
        """Tests midair collisions for non-ajax submissions."""
        self.client.login(username='admin', password='testpass')

        # Post a new document.
        data = new_document_data()
        resp = self.client.post(reverse('wiki.create'), data,
                                HTTP_HOST=settings.WIKI_HOST)
        doc = Document.objects.get(slug=data['slug'])
        # This is the url to post new revisions for the rest of this test
        posting_url = reverse('wiki.edit', args=[doc.slug])

        # Edit #1 starts...
        resp = self.client.get(reverse('wiki.edit', args=[doc.slug]),
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')
        # Edit #2 starts...
        resp = self.client.get(reverse('wiki.edit', args=[doc.slug]),
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Update data for the POST we are about to attempt
        data.update({
            'form-type': 'rev',
            'content': 'This edit got there first',
            'current_rev': rev_id2
        })
        # If this is a translation test, then create a translation and a
        # revision on it. Then update data.
        if translate_locale:
            translation = document(parent=doc, locale=translate_locale, save=True)
            translation_rev = revision(
                document=translation,
                based_on=translation.parent.current_or_latest_revision(),
                save=True
            )
            rev_id1 = rev_id2 = translation_rev.id
            posting_url = reverse(
                'wiki.edit',
                args=[translation_rev.document.slug],
                locale=translate_locale
            )
            data.update({
                'title': translation.title,
                'locale': translation.locale,
                'slug': translation.slug,
                'current_rev': rev_id2
            })

        # Edit #2 submits successfully
        if is_ajax:
            resp = self.client.post(
                posting_url,
                data, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                HTTP_HOST=settings.WIKI_HOST
            )
            assert resp.status_code == 200
            assert not json.loads(resp.content)['error']
        else:
            resp = self.client.post(posting_url, data,
                                    HTTP_HOST=settings.WIKI_HOST)
            assert resp.status_code == 302

        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

        # Edit #1 submits, but receives a mid-aired notification
        data.update({
            'form-type': 'rev',
            'content': 'This edit gets mid-aired',
            'current_rev': rev_id1
        })
        if is_ajax:
            resp = self.client.post(
                posting_url,
                data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                HTTP_HOST=settings.WIKI_HOST
            )
        else:
            resp = self.client.post(posting_url, data,
                                    HTTP_HOST=settings.WIKI_HOST)

        # The url of the document's history
        locale = translate_locale if translate_locale else doc.locale
        doc_path = translation.slug if translate_locale else doc.slug
        history_url = reverse(
            'wiki.document_revisions', kwargs={'document_path': doc_path}, locale=locale
        )
        # The midair collission error, with the document url
        midair_collission_error = (unicode(
            MIDAIR_COLLISION) % {'url': history_url}
        ).encode('utf-8')

        if is_ajax:
            location_of_error = json.loads(resp.content)['error_message']
        else:
            # If this is not an ajax post, then the error comes back in escaped
            # html. We unescape the resp.content, but not all of it, since that
            # causes ascii errors.
            start_of_error = resp.content.index(midair_collission_error[0:20])
            # Add an some extra characters to the end, since the unescaped length
            # is a little less than the escaped length
            end_of_error = start_of_error + len(midair_collission_error) + 20
            location_of_error = html_parser.HTMLParser().unescape(
                resp.content[start_of_error: end_of_error]
            )
        assert midair_collission_error in location_of_error

    @pytest.mark.midair
    def test_edit_midair_collisions_ajax(self):
        """Tests midair collisions for ajax submissions."""
        self.test_edit_midair_collisions(is_ajax=True)

    @override_flag(SPAM_SUBMISSIONS_FLAG, active=True)
    @override_flag(SPAM_CHECKS_FLAG, active=True)
    @override_config(AKISMET_KEY='dashboard')
    @requests_mock.mock()
    @mock.patch('kuma.spam.akismet.Akismet.check_comment')
    def test_edit_spam_ajax(self, mock_requests, mock_akismet_method, translate_locale=None):
        """Tests attempted spam edits that occur on Ajax POSTs."""
        # Note: Akismet is enabled by the Flag overrides

        mock_requests.post(VERIFY_URL, content='valid')
        # The return value of akismet.check_comment is set to True
        mock_akismet_method.return_value = True

        # self.client.login(username='admin', password='testpass')
        self.client.login(username='testuser', password='testpass')

        # Create a new document.
        doc = document(save=True)
        data = new_document_data()
        # Create a revision on the document
        revision(save=True, document=doc)
        # This is the url to post new revisions for the rest of this test
        posting_url = reverse('wiki.edit', args=[doc.slug])

        # If this is a translation test, then create a translation and a revision on it
        if translate_locale:
            data['locale'] = translate_locale
            translation = document(
                parent=doc,
                locale=translate_locale,
                save=True
            )
            translation_rev = revision(
                document=translation,
                based_on=translation.parent.current_or_latest_revision(),
                save=True
            )
            # rev_id = translation_rev.id
            posting_url = reverse(
                'wiki.edit',
                args=[translation_rev.document.slug],
                locale=translate_locale
            )

        # Get the rev id
        resp = self.client.get(posting_url, HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id = page.find('input[name="current_rev"]').attr('value')

        # Edit submits
        data.update({
            'form-type': 'rev',
            'content': 'Spam content',
            'current_rev': rev_id
        })
        resp = self.client.post(
            posting_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_HOST=settings.WIKI_HOST
        )

        spam_message = render_to_string('wiki/includes/spam_error.html')
        assert spam_message in json.loads(resp.content)['error_message']

    def test_multiple_edits_ajax(self, translate_locale=None):
        """Tests multiple sequential attempted valid edits that occur as Ajax POSTs."""

        self.client.login(username='admin', password='testpass')

        # Post a new document.
        data = new_document_data()
        resp = self.client.post(reverse('wiki.create'), data,
                                HTTP_HOST=settings.WIKI_HOST)
        doc = Document.objects.get(slug=data['slug'])
        # This is the url to post new revisions for the rest of this test
        if translate_locale:
            posting_url = reverse('wiki.edit', args=[doc.slug], locale=translate_locale)
        else:
            posting_url = reverse('wiki.edit', args=[doc.slug])

        if translate_locale:
            # Post a new translation on doc
            translate_url = reverse(
                'wiki.translate',
                args=[data['slug']]
            ) + '?tolocale={}'.format(translate_locale)
            self.client.post(translate_url, data, follow=True,
                             HTTP_HOST=settings.WIKI_HOST)
            data.update({'locale': translate_locale})

        # Edit #1
        resp = self.client.get(posting_url, HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #1 submits successfully
        data.update({
            'form-type': 'rev',
            'content': 'Edit #1',
            'current_rev': rev_id1
        })
        resp1 = self.client.post(
            posting_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_HOST=settings.WIKI_HOST
        )

        # Edit #2
        resp = self.client.get(posting_url, HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form-type': 'rev',
            'content': 'Edit #2',
            'current_rev': rev_id2
        })
        resp2 = self.client.post(
            posting_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_HOST=settings.WIKI_HOST
        )

        # For Ajax requests the response is a JsonResponse
        for resp in [resp1, resp2]:
            assert not json.loads(resp.content)['error']
            assert 'error_message' not in json.loads(resp.content).keys()

    def test_multiple_translation_edits_ajax(self):
        """Tests multiple sequential valid transalation edits that occur as Ajax POSTs."""
        self.test_multiple_edits_ajax(translate_locale='es')

    # test translation fails as well
    def test_translation_midair_collission(self):
        """Tests midair collisions for non-ajax translation revisions."""
        self.test_edit_midair_collisions(is_ajax=False, translate_locale='ca')

    def test_translation_midair_collission_ajax(self):
        """Tests midair collisions for ajax translation revisions."""
        self.test_edit_midair_collisions(is_ajax=True, translate_locale='it')

    def test_translation_spam_ajax(self):
        """Tests attempted translation spam edits that occur on Ajax POSTs."""
        self.test_edit_spam_ajax(translate_locale='ru')

    @pytest.mark.toc
    def test_toc_toggle_off(self):
        """Toggling of table of contents in revisions"""
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True)
        doc = rev.document
        data = new_document_data()
        assert Document.objects.get(slug=doc.slug, locale=doc.locale).show_toc
        data['form-type'] = 'rev'
        data['toc_depth'] = 0
        data['slug'] = doc.slug
        data['title'] = doc.title
        resp = self.client.post(reverse('wiki.edit', args=[doc.slug]), data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        doc = Document.objects.get(slug=doc.slug, locale=doc.locale)
        assert doc.current_revision.toc_depth == 0

    @pytest.mark.toc
    def test_toc_toggle_on(self):
        """Toggling of table of contents in revisions"""
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True)
        new_r = revision(document=rev.document, content=rev.content,
                         toc_depth=0, is_approved=True)
        new_r.save()
        assert not Document.objects.get(slug=rev.document.slug,
                                        locale=rev.document.locale).show_toc
        data = new_document_data()
        data['form-type'] = 'rev'
        data['slug'] = rev.document.slug
        data['title'] = rev.document.title
        resp = self.client.post(reverse('wiki.edit', args=[rev.document.slug]),
                                data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        assert Document.objects.get(slug=rev.document.slug,
                                    locale=rev.document.locale).show_toc

    def test_parent_topic(self):
        """Selection of a parent topic when creating a document."""
        # TODO: Do we need this test? This seems broken in that the
        #       parent specified via the parent topic doesn't get it's
        #       slug prepended to the new document's slug, as happens
        #       when specifying the parent via the URL.
        self.client.login(username='admin', password='testpass')
        doc = document(title='HTML8')
        doc.save()
        rev = revision(document=doc)
        rev.save()

        data = new_document_data()
        data['title'] = 'Replicated local storage'
        data['parent_topic'] = doc.id
        resp = self.client.post(reverse('wiki.create'), data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        assert doc.children.count() == 1
        assert doc.children.all()[0].title == 'Replicated local storage'

    def test_repair_breadcrumbs(self):
        english_top = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                               title='English top',
                               save=True)
        english_mid = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                               title='English mid',
                               parent_topic=english_top,
                               save=True)
        english_bottom = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                  title='English bottom',
                                  parent_topic=english_mid,
                                  save=True)

        french_top = document(locale='fr',
                              title='French top',
                              parent=english_top,
                              save=True)
        french_mid = document(locale='fr',
                              title='French mid',
                              parent=english_mid,
                              parent_topic=english_mid,
                              save=True)
        french_bottom = document(locale='fr',
                                 title='French bottom',
                                 parent=english_bottom,
                                 parent_topic=english_bottom,
                                 save=True)

        self.client.login(username='admin', password='testpass')

        resp = self.client.get(reverse('wiki.repair_breadcrumbs',
                                       args=[french_bottom.slug],
                                       locale='fr'),
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert_no_cache_header(resp)
        assert french_bottom.get_absolute_url() in resp['Location']

        french_bottom_fixed = Document.objects.get(locale='fr',
                                                   title=french_bottom.title)
        assert french_mid.id == french_bottom_fixed.parent_topic.id
        assert (french_top.id ==
                french_bottom_fixed.parent_topic.parent_topic.id)

    def test_translate_on_edit(self):
        d1 = document(title="Doc1", locale=settings.WIKI_DEFAULT_LANGUAGE,
                      save=True)
        revision(document=d1, save=True)

        d2 = document(title="TransDoc1", locale='de', parent=d1, save=True)
        revision(document=d2, save=True)

        self.client.login(username='admin', password='testpass')
        url = reverse('wiki.edit', args=(d2.slug,), locale=d2.locale)

        resp = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

    def test_discard_location(self):
        """Testing that the 'discard' HREF goes to the correct place when it's
           explicitely and implicitely set"""

        self.client.login(username='admin', password='testpass')

        def _create_doc(slug, locale):
            doc = document(slug=slug, is_localizable=True, locale=locale)
            doc.save()
            r = revision(document=doc)
            r.save()
            return doc

        # Test that the 'discard' button on an edit goes to the original page
        doc = _create_doc('testdiscarddoc', settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(reverse('wiki.edit', args=[doc.slug]),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert (pq(response.content).find('.btn-discard').attr('href') ==
                reverse('wiki.document', args=[doc.slug]))

        # Test that the 'discard button on a new translation goes
        # to the en-US page'
        response = self.client.get(reverse('wiki.translate', args=[doc.slug]),
                                   {'tolocale': 'es'},
                                   HTTP_HOST=settings.WIKI_HOST)
        assert (pq(response.content).find('.btn-discard').attr('href') ==
                reverse('wiki.document', args=[doc.slug]))

        # Test that the 'discard' button on an existing translation goes
        # to the 'es' page
        foreign_doc = _create_doc('testdiscarddoc', 'es')
        response = self.client.get(reverse('wiki.edit',
                                           args=[foreign_doc.slug],
                                           locale=foreign_doc.locale),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert (pq(response.content).find('.btn-discard').attr('href') ==
                reverse('wiki.document', args=[foreign_doc.slug],
                        locale=foreign_doc.locale))

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get',
                return_value=('lorem ipsum dolor sit amet', None))
    def test_revert(self, mock_kumascript_get):
        self.client.login(username='admin', password='testpass')

        data = new_document_data()
        data['title'] = 'A Test Article For Reverting'
        data['slug'] = 'test-article-for-reverting'
        response = self.client.post(reverse('wiki.create'), data,
                                    HTTP_HOST=settings.WIKI_HOST)

        doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                   slug='test-article-for-reverting')
        rev = doc.revisions.order_by('-id').all()[0]

        data['content'] = 'Not lorem ipsum anymore'
        data['comment'] = 'Nobody likes Latin anyway'

        response = self.client.post(reverse('wiki.edit', args=[doc.slug]), data,
                                    HTTP_HOST=settings.WIKI_HOST)

        mock_kumascript_get.reset_mock()
        response = self.client.post(reverse('wiki.revert_document',
                                            args=[doc.slug, rev.id]),
                                    {'revert': True, 'comment': 'Blah blah'},
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert_no_cache_header(response)
        assert mock_kumascript_get.called, "kumascript should have been used"
        rev = doc.revisions.order_by('-id').all()[0]
        assert rev.content == 'lorem ipsum dolor sit amet'
        assert 'Blah blah' in rev.comment

        mock_kumascript_get.reset_mock()
        rev = doc.revisions.order_by('-id').all()[1]
        response = self.client.post(reverse('wiki.revert_document',
                                            args=[doc.slug, rev.id]),
                                    {'revert': True},
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        rev = doc.revisions.order_by('-id').all()[0]
        assert ': ' not in rev.comment
        assert mock_kumascript_get.called, "kumascript should have been used"

    def test_revert_moved(self):
        doc = document(slug='move-me', save=True)
        rev = revision(document=doc, save=True)
        prev_rev_id = rev.id
        doc._move_tree('moved-doc')
        self.client.login(username='admin', password='testpass')

        resp = self.client.post(reverse('wiki.revert_document',
                                        args=[doc.slug, prev_rev_id]),
                                HTTP_HOST=settings.WIKI_HOST)

        assert resp.status_code == 200
        assert_no_cache_header(resp)
        assert b'cannot revert a document that has been moved' in resp.content

    def test_store_revision_ip(self):
        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        slug = 'test-article-for-storing-revision-ip'
        data.update({'title': 'A Test Article For Storing Revision IP',
                     'slug': slug})
        self.client.post(reverse('wiki.create'), data,
                         HTTP_HOST=settings.WIKI_HOST)

        doc = Document.objects.get(locale='en-US', slug=slug)

        data.update({'form-type': 'rev',
                     'content': 'This revision should NOT record IP',
                     'comment': 'This revision should NOT record IP'})

        resp = self.client.post(reverse('wiki.edit', args=[doc.slug]),
                                data,
                                HTTP_USER_AGENT='Mozilla Firefox',
                                HTTP_REFERER='http://localhost/',
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        assert RevisionIP.objects.all().count() == 0

        data.update({'content': 'Store the IP address for the revision.',
                     'comment': 'Store the IP address for the revision.'})

        with override_switch('store_revision_ips', True):
            self.client.post(reverse('wiki.edit', args=[doc.slug]),
                             data,
                             HTTP_USER_AGENT='Mozilla Firefox',
                             HTTP_REFERER='http://localhost/',
                             HTTP_HOST=settings.WIKI_HOST)
        assert RevisionIP.objects.all().count() == 1
        rev = doc.revisions.order_by('-id').all()[0]
        rev_ip = RevisionIP.objects.get(revision=rev)
        assert rev_ip.ip == '127.0.0.1'
        assert rev_ip.user_agent == 'Mozilla Firefox'
        assert rev_ip.referrer == 'http://localhost/'

    @pytest.mark.edit_emails
    @call_on_commit_immediately
    def test_email_for_first_edits(self):
        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        slug = 'test-article-for-storing-revision-ip'
        data.update({'title': 'A Test Article For First Edit Emails',
                     'slug': slug})
        self.client.post(reverse('wiki.create'), data,
                         HTTP_HOST=settings.WIKI_HOST)
        assert len(mail.outbox) == 1

        doc = Document.objects.get(
            locale=settings.WIKI_DEFAULT_LANGUAGE, slug=slug)

        data.update({'form-type': 'rev',
                     'content': 'This edit should not send an email',
                     'comment': 'This edit should not send an email'})

        resp = self.client.post(reverse('wiki.edit', args=[doc.slug]), data,
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

        assert len(mail.outbox) == 1

        self.client.login(username='admin', password='testpass')
        data.update({'content': 'Admin first edit should send an email',
                     'comment': 'Admin first edit should send an email'})

        self.client.post(reverse('wiki.edit',
                                 args=[doc.slug]),
                         data, HTTP_HOST=settings.WIKI_HOST)
        assert len(mail.outbox) == 2

        def _check_message_for_headers(message, username):
            assert "%s made their first edit" % username in message.subject
            assert message.extra_headers == {
                'X-Kuma-Document-Url': doc.get_full_url(),
                'X-Kuma-Editor-Username': username,
                'X-Kuma-Document-Locale': doc.locale,
                'X-Kuma-Document-Title': doc.title
            }

        testuser_message = mail.outbox[0]
        admin_message = mail.outbox[1]
        _check_message_for_headers(testuser_message, 'testuser')
        _check_message_for_headers(admin_message, 'admin')

    def test_email_for_watched_edits(self):
        """
        When a user edits a watched document, we should send an email to users
        who are watching it.
        """
        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        rev = revision(save=True)
        previous_rev = rev.previous

        testuser2 = get_user(username='testuser2')
        EditDocumentEvent.notify(testuser2, rev.document)

        data.update({'form-type': 'rev',
                     'slug': rev.document.slug,
                     'title': rev.document.title,
                     'content': 'This edit should send an email',
                     'comment': 'This edit should send an email'})
        resp = self.client.post(reverse('wiki.edit', args=[rev.document.slug]),
                                data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

        self.assertEquals(1, len(mail.outbox))
        message = mail.outbox[0]
        assert testuser2.email in message.to
        assert str(rev.document.title) in message.body
        assert 'sub-articles' not in message.body
        # Test that the compare URL points to the right revisions
        rev = Document.objects.get(pk=rev.document_id).current_revision
        assert rev.id != previous_rev
        assert (add_utm(get_compare_url(rev.document, rev.previous.id, rev.id),
                        'Wiki Doc Edits')
                in message.body)

        # Subscribe another user and assert 2 emails sent this time
        mail.outbox = []
        testuser01 = get_user(username='testuser01')
        EditDocumentEvent.notify(testuser01, rev.document)

        data.update({'form-type': 'rev',
                     'slug': rev.document.slug,
                     'content': 'This edit should send 2 emails',
                     'comment': 'This edit should send 2 emails'})
        self.client.post(reverse('wiki.edit',
                                 args=[rev.document.slug]),
                         data, HTTP_HOST=settings.WIKI_HOST)
        self.assertEquals(2, len(mail.outbox))
        message = mail.outbox[0]
        assert testuser2.email in message.to
        assert rev.document.title in message.body
        assert 'sub-articles' not in message.body

        message = mail.outbox[1]
        assert testuser01.email in message.to
        assert rev.document.title in message.body
        assert 'sub-articles' not in message.body

    @pytest.mark.edit_emails
    def test_email_for_child_edit_in_watched_tree(self):
        """
        When a user edits a child document in a watched document tree, we
        should send an email to users who are watching the tree.
        """
        root_doc, child_doc, grandchild_doc = create_document_tree()

        testuser2 = get_user(username='testuser2')
        EditDocumentInTreeEvent.notify(testuser2, root_doc)

        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        data.update({'form-type': 'rev',
                     'slug': child_doc.slug,
                     'content': 'This edit should send an email',
                     'comment': 'This edit should send an email'})
        resp = self.client.post(reverse('wiki.edit', args=[child_doc.slug]),
                                data, HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 302
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert testuser2.email in message.to
        assert 'sub-articles' in message.body

    @pytest.mark.edit_emails
    def test_email_for_grandchild_edit_in_watched_tree(self):
        """
        When a user edits a grandchild document in a watched document tree, we
        should send an email to users who are watching the tree.
        """
        root_doc, child_doc, grandchild_doc = create_document_tree()

        testuser2 = get_user(username='testuser2')
        EditDocumentInTreeEvent.notify(testuser2, root_doc)

        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        data.update({'form-type': 'rev',
                     'slug': grandchild_doc.slug,
                     'content': 'This edit should send an email',
                     'comment': 'This edit should send an email'})
        self.client.post(reverse('wiki.edit',
                                 args=[grandchild_doc.slug]),
                         data, HTTP_HOST=settings.WIKI_HOST)
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert testuser2.email in message.to
        assert 'sub-articles' in message.body

    @pytest.mark.edit_emails
    def test_single_email_when_watching_doc_and_tree(self):
        """
        When a user edits a watched document in a watched document tree, we
        should only send a single email to users who are watching both the
        document and the tree.
        """
        root_doc, child_doc, grandchild_doc = create_document_tree()

        testuser2 = get_user(username='testuser2')
        EditDocumentInTreeEvent.notify(testuser2, root_doc)
        EditDocumentEvent.notify(testuser2, child_doc)

        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        data.update({'form-type': 'rev',
                     'slug': child_doc.slug,
                     'content': 'This edit should send an email',
                     'comment': 'This edit should send an email'})
        self.client.post(reverse('wiki.edit',
                                 args=[child_doc.slug]),
                         data, HTTP_HOST=settings.WIKI_HOST)
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert testuser2.email in message.to


class SectionEditingResourceTests(UserTestCase, WikiTestCase):

    def test_raw_source(self):
        """The raw source for a document can be requested"""
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True, content="""
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
        with override_switch('application_ACAO', True):
            response = self.client.get('%s?raw=true' %
                                       reverse('wiki.document',
                                               args=[rev.document.slug]),
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                       HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        assert response['Access-Control-Allow-Origin'] == '*'
        assert normalize_html(expected) == normalize_html(response.content)

    def test_raw_editor_safety_filter(self):
        """Safety filter should be applied before rendering editor

        bug 821986
        """
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True, content="""
            <p onload=alert(3)>FOO</p>
            <svg><circle onload=confirm(3)>HI THERE</circle></svg>
        """)
        response = self.client.get('%s?raw=true' %
                                   reverse('wiki.document',
                                           args=[rev.document.slug]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        assert b'<p onload=' not in response.content
        assert b'<circle onload=' not in response.content

    def test_raw_with_editing_links_source(self):
        """The raw source for a document can be requested, with section editing
        links"""
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True, content="""
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
            <h1 id="s1"><a class="edit-section" data-section-id="s1" data-section-src-url="/en-US/docs/%(slug)s?raw=true&amp;section=s1" href="/en-US/docs/%(slug)s$edit?edit_links=true&amp;section=s1" title="Edit section">Edit</a>s1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2"><a class="edit-section" data-section-id="s2" data-section-src-url="/en-US/docs/%(slug)s?raw=true&amp;section=s2" href="/en-US/docs/%(slug)s$edit?edit_links=true&amp;section=s2" title="Edit section">Edit</a>s2</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s3"><a class="edit-section" data-section-id="s3" data-section-src-url="/en-US/docs/%(slug)s?raw=true&amp;section=s3" href="/en-US/docs/%(slug)s$edit?edit_links=true&amp;section=s3" title="Edit section">Edit</a>s3</h1>
            <p>test</p>
            <p>test</p>
        """ % {'slug': rev.document.slug}

        response = self.client.get('%s?raw=true&edit_links=true' %
                                   reverse('wiki.document',
                                           args=[rev.document.slug]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        assert normalize_html(expected) == normalize_html(response.content)

    def test_raw_section_source(self):
        """The raw source for a document section can be requested"""
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True, content="""
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
        response = self.client.get('%s?section=s2&raw=true' %
                                   reverse('wiki.document',
                                           args=[rev.document.slug]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        assert normalize_html(expected) == normalize_html(response.content)

    @pytest.mark.midair
    def test_raw_section_edit_ajax(self):
        self.client.login(username='admin', password='testpass')
        rev = revision(is_approved=True, save=True, content="""
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
        replace = """
            <h1 id="s2">s2</h1>
            <p>replace</p>
        """
        response = self.client.post('%s?section=s2&raw=true' %
                                    reverse('wiki.edit',
                                            args=[rev.document.slug]),
                                    {"form-type": "rev",
                                     "slug": rev.document.slug,
                                     "content": replace},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert json.loads(response.content) == {
            'error': False,
            'new_revision_id': rev.id + 1
        }

        expected = """
            <h1 id="s1">s1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">s2</h1>
            <p>replace</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """
        response = self.client.get('%s?raw=true' %
                                   reverse('wiki.document',
                                           args=[rev.document.slug]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        assert normalize_html(expected) == normalize_html(response.content)

    @pytest.mark.midair
    def test_midair_section_merge_ajax(self):
        """If a page was changed while someone was editing, but the changes
        didn't affect the specific section being edited, then ignore the midair
        warning"""
        self.client.login(username='admin', password='testpass')

        rev = revision(is_approved=True, save=True, content="""
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
        replace_1 = """
            <h1 id="replace1">replace1</h1>
            <p>replace</p>
        """
        replace_2 = """
            <h1 id="replace2">replace2</h1>
            <p>replace</p>
        """
        expected = """
            <h1 id="replace1">replace1</h1>
            <p>replace</p>

            <h1 id="replace2">replace2</h1>
            <p>replace</p>

            <h1 id="s3">s3</h1>
            <p>test</p>
            <p>test</p>
        """
        data = {
            'form-type': 'rev',
            'content': rev.content,
            'slug': ''
        }

        # Edit #1 starts...
        resp = self.client.get('%s?section=s1' %
                               reverse('wiki.edit',
                                       args=[rev.document.slug]),
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = self.client.get('%s?section=s2' %
                               reverse('wiki.edit',
                                       args=[rev.document.slug]),
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form-type': 'rev',
            'content': replace_2,
            'current_rev': rev_id2,
            'slug': rev.document.slug
        })
        resp = self.client.post('%s?section=s2&raw=true' %
                                reverse('wiki.edit',
                                        args=[rev.document.slug]),
                                data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert resp['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(resp)

        assert not json.loads(resp.content)['error']

        # Edit #1 submits, but since it's a different section, there's no
        # mid-air collision
        data.update({
            'form-type': 'rev',
            'content': replace_1,
            'current_rev': rev_id1
        })
        resp = self.client.post('%s?section=s1&raw=true' %
                                reverse('wiki.edit', args=[rev.document.slug]),
                                data,
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                HTTP_HOST=settings.WIKI_HOST)
        # No conflict, but we should get a 205 Reset as an indication that the
        # page needs a refresh.
        assert resp.status_code == 205

        # Finally, make sure that all the edits landed
        response = self.client.get('%s?raw=true' %
                                   reverse('wiki.document',
                                           args=[rev.document.slug]),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        # Since the client is logged-in, the response should not be cached.
        assert_no_cache_header(response)
        assert normalize_html(expected) == normalize_html(response.content)

        # Also, ensure that the revision is slipped into the headers
        assert (unicode(Document.objects.get(slug=rev.document.slug,
                                             locale=rev.document.locale)
                                        .current_revision.id) ==
                unicode(response['x-kuma-revision']))

    @pytest.mark.midair
    def test_midair_section_collision_ajax(self):
        """If both a revision and the edited section has changed, then a
        section edit is a collision."""
        self.client.login(username='admin', password='testpass')

        rev = revision(is_approved=True, save=True, content="""
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
        replace_1 = """
            <h1 id="s2">replace</h1>
            <p>replace</p>
        """
        replace_2 = """
            <h1 id="s2">first replace</h1>
            <p>first replace</p>
        """
        data = {
            'form-type': 'rev',
            'content': rev.content
        }

        # Edit #1 starts...
        resp = self.client.get('%s?section=s2' %
                               reverse('wiki.edit', args=[rev.document.slug]),
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = self.client.get('%s?section=s2' %
                               reverse('wiki.edit', args=[rev.document.slug]),
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                               HTTP_HOST=settings.WIKI_HOST)
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form-type': 'rev',
            'content': replace_2,
            'slug': rev.document.slug,
            'current_rev': rev_id2
        })
        resp = self.client.post('%s?section=s2&raw=true' %
                                reverse('wiki.edit', args=[rev.document.slug]),
                                data, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                HTTP_HOST=settings.WIKI_HOST)
        assert not json.loads(resp.content)['error']

        # Edit #1 submits, but since it's the same section, there's a collision
        data.update({
            'form': 'rev',
            'content': replace_1,
            'current_rev': rev_id1
        })
        resp = self.client.post('%s?section=s2&raw=true' %
                                reverse('wiki.edit', args=[rev.document.slug]),
                                data, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                HTTP_HOST=settings.WIKI_HOST)
        assert 200 == resp.status_code
        # We receive the midair collission message
        history_url = reverse(
            'wiki.document_revisions',
            kwargs={'document_path': rev.document.slug})
        midair_collission_error = (unicode(MIDAIR_COLLISION) % {'url': history_url}).encode('utf-8')
        assert midair_collission_error in json.loads(resp.content)['error_message']

    def test_raw_include_option(self):
        doc_src = u"""
            <div class="noinclude">{{ XULRefAttr() }}</div>
            <dl>
              <dt>{{ XULAttr(&quot;maxlength&quot;) }}</dt>
              <dd>Type: <em>integer</em></dd>
              <dd>Przykłady 例 예제 示例</dd>
            </dl>
            <p><iframe></iframe></p>
            <div class="noinclude">
              <p>{{ languages( { &quot;ja&quot;: &quot;ja/XUL/Attribute/maxlength&quot; } ) }}</p>
            </div>
        """
        rev = revision(is_approved=True, save=True, content=doc_src)
        expected = u"""
            <dl>
              <dt>{{ XULAttr(&quot;maxlength&quot;) }}</dt>
              <dd>Type: <em>integer</em></dd>
              <dd>Przykłady 例 예제 示例</dd>
            </dl>
            <p><iframe></iframe></p>
        """
        resp = self.client.get('%s?raw&include' %
                               reverse('wiki.document',
                                       args=[rev.document.slug]),
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200
        assert_shared_cache_header(resp)
        assert (normalize_html(expected) ==
                normalize_html(resp.content.decode('utf-8')))

    def test_section_edit_toc(self):
        """show_toc is preserved in section editing."""
        self.client.login(username='admin', password='testpass')

        rev = revision(is_approved=True, save=True, content="""
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
        rev.toc_depth = 1
        rev.save()

        replace = """
        <h1 id="s2">s2</h1>
        <p>replace</p>
        """
        self.client.post('%s?section=s2&raw=true' %
                         reverse('wiki.edit', args=[rev.document.slug]),
                         {"form-type": "rev", "slug": rev.document.slug, "content": replace},
                         follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                         HTTP_HOST=settings.WIKI_HOST)
        changed = Document.objects.get(pk=rev.document.id).current_revision
        assert rev.id != changed.id
        assert 1 == changed.toc_depth

    def test_section_edit_review_tags(self):
        """review tags are preserved in section editing."""
        self.client.login(username='admin', password='testpass')

        rev = revision(is_approved=True, save=True, content="""
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
        tags_to_save = ['bar', 'foo']
        rev.save()
        rev.review_tags.set(*tags_to_save)

        replace = """
        <h1 id="s2">s2</h1>
        <p>replace</p>
        """
        self.client.post('%s?section=s2&raw=true' %
                         reverse('wiki.edit', args=[rev.document.slug]),
                         {"form-type": "rev", "slug": rev.document.slug, "content": replace},
                         follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                         HTTP_HOST=settings.WIKI_HOST)
        changed = Document.objects.get(pk=rev.document.id).current_revision
        assert rev.id != changed.id
        assert set(tags_to_save) == set(t.name for t in changed.review_tags.all())


class MindTouchRedirectTests(UserTestCase, WikiTestCase):
    """
    Test that we appropriately redirect old-style MindTouch URLs to
    new-style kuma URLs.

    """
    # A note on these tests: we could try to use assertRedirects on
    # these, but for the most part we're just constructing a URL
    # similar enough to the wiki app's own built-in redirects that
    # it'll pick up the request and do what we want with it. But it
    # may end up issuing its own redirects, which are tricky to sort
    # out from the ones the legacy MindTouch handling will emit, so
    # instead we just test that A) we did issue a redirect and B) the
    # URL we constructed is enough for the document views to go on.

    server_prefix = '/%s/docs' % settings.WIKI_DEFAULT_LANGUAGE
    namespace_urls = (
        # One for each namespace.
        {'mindtouch': '/Help:Foo',
         'kuma': '%s/Help:Foo' % server_prefix},
        {'mindtouch': '/Help_talk:Foo',
         'kuma': '%s/Help_talk:Foo' % server_prefix},
        {'mindtouch': '/Project:En/MDC_editor_guide',
         'kuma': '%s/Project:MDC_editor_guide' % server_prefix},
        {'mindtouch': '/Project_talk:En/MDC_style_guide',
         'kuma': '%s/Project_talk:MDC_style_guide' % server_prefix},
        {'mindtouch': '/Special:Foo',
         'kuma': '%s/Special:Foo' % server_prefix},
        {'mindtouch': '/Talk:en/Foo',
         'kuma': '%s/Talk:Foo' % server_prefix},
        {'mindtouch': '/Template:Foo',
         'kuma': '%s/Template:Foo' % server_prefix},
        {'mindtouch': '/User:Foo',
         'kuma': '%s/User:Foo' % server_prefix},
    )

    def test_namespace_urls(self):
        new_doc = document()
        new_doc.title = 'User:Foo'
        new_doc.slug = 'User:Foo'
        new_doc.save()
        for namespace_test in self.namespace_urls:
            resp = self.client.get(namespace_test['mindtouch'], follow=False)
            assert 301 == resp.status_code
            assert resp['Location'] == namespace_test['kuma']

    def test_document_urls(self):
        """Check the url redirect to proper document when the url like
         /<locale>/<document_slug>"""
        d = document(locale='zh-CN')
        d.save()
        mt_url = '/{locale}/{slug}'.format(locale=d.locale, slug=d.slug)
        resp = self.client.get(mt_url, follow=True,
                               HTTP_HOST=settings.WIKI_HOST)
        assert resp.status_code == 200

        # Check the last redirect chain url is correct document url
        last_url = resp.redirect_chain[-1][0]
        assert last_url == d.get_absolute_url()

    def test_view_param(self):
        d = document()
        d.locale = settings.WIKI_DEFAULT_LANGUAGE
        d.slug = 'HTML/HTML5'
        d.title = 'HTML 5'
        d.save()
        mt_url = '/en-US/%s?view=edit' % (d.slug,)
        resp = self.client.get(mt_url, HTTP_HOST=settings.WIKI_HOST)
        assert 301 == resp.status_code
        expected_url = d.get_absolute_url('wiki.edit')
        assert resp['Location'] == expected_url


@override_config(KUMASCRIPT_TIMEOUT=5.0, KUMASCRIPT_MAX_AGE=600)
class DeferredRenderingViewTests(UserTestCase, WikiTestCase):
    """Tests for the deferred rendering system and interaction with views"""

    def setUp(self):
        super(DeferredRenderingViewTests, self).setUp()
        self.rendered_content = 'HELLO RENDERED CONTENT'
        self.raw_content = 'THIS IS RAW CONTENT'

        self.rev = revision(is_approved=True, save=True,
                            content=self.raw_content,
                            # Disable TOC, makes content inspection easier.
                            toc_depth=0)
        self.doc = self.rev.document
        self.doc.html = self.raw_content
        self.doc.rendered_html = self.rendered_content
        self.doc.save()

        self.url = self.doc.get_absolute_url()

    @mock.patch('kuma.wiki.kumascript.get')
    def test_rendered_content(self, mock_kumascript_get):
        """Document view should serve up rendered content when available"""
        mock_kumascript_get.return_value = (self.rendered_content, None)
        resp = self.client.get(self.url, follow=False,
                               HTTP_HOST=settings.WIKI_HOST)
        p = pq(resp.content)
        txt = p.find('#wikiArticle').text()
        assert self.rendered_content in txt
        assert self.raw_content not in txt

        assert 0 == p.find('#doc-rendering-in-progress').length
        assert 0 == p.find('#doc-render-raw-fallback').length

    def test_rendering_in_progress_warning(self):
        # Make the document look like there's a rendering in progress.
        self.doc.render_started_at = datetime.datetime.now()
        self.doc.save()

        resp = self.client.get(self.url, follow=False,
                               HTTP_HOST=settings.WIKI_HOST)
        p = pq(resp.content)
        txt = p.find('#wikiArticle').text()

        # Even though a rendering looks like it's in progress, ensure the
        # last-known render is displayed.
        assert self.rendered_content in txt
        assert self.raw_content not in txt
        assert 0 == p.find('#doc-rendering-in-progress').length

        # Only for logged-in users, ensure the render-in-progress warning is
        # displayed.
        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.url, follow=False,
                               HTTP_HOST=settings.WIKI_HOST)
        p = pq(resp.content)
        assert 1 == p.find('#doc-rendering-in-progress').length

    @mock.patch('kuma.wiki.kumascript.get')
    def test_raw_content_during_initial_render(self, mock_kumascript_get):
        """Raw content should be displayed during a document's initial
        deferred rendering"""
        mock_kumascript_get.return_value = (self.rendered_content, None)

        # Make the document look like there's no rendered content, but that a
        # rendering is in progress.
        self.doc.html = self.raw_content
        self.doc.rendered_html = ''
        self.doc.render_started_at = datetime.datetime.now()
        self.doc.save()

        # Now, ensure that raw content is shown in the view.
        resp = self.client.get(self.url, follow=False,
                               HTTP_HOST=settings.WIKI_HOST)
        p = pq(resp.content)
        txt = p.find('#wikiArticle').text()
        assert self.rendered_content not in txt
        assert self.raw_content in txt
        assert 0 == p.find('#doc-render-raw-fallback').length

        # Only for logged-in users, ensure that a warning is displayed about
        # the fallback
        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.url, follow=False,
                               HTTP_HOST=settings.WIKI_HOST)
        p = pq(resp.content)
        assert 1 == p.find('#doc-render-raw-fallback').length

    @mock.patch.object(Document, 'schedule_rendering')
    @mock.patch('kuma.wiki.kumascript.get')
    def test_schedule_rendering(self, mock_kumascript_get,
                                mock_document_schedule_rendering):
        mock_kumascript_get.return_value = (self.rendered_content, None)

        self.client.login(username='testuser', password='testpass')

        data = new_document_data()
        data.update({
            'form-type': 'rev',
            'content': 'This is an update',
        })

        edit_url = reverse('wiki.edit', args=[self.doc.slug])
        resp = self.client.post(edit_url, data, HTTP_HOST=settings.WIKI_HOST)
        assert 302 == resp.status_code
        assert mock_document_schedule_rendering.called

        mock_document_schedule_rendering.reset_mock()

        data.update({
            'form-type': 'both',
            'content': 'This is a translation',
        })
        translate_url = (reverse('wiki.translate', args=[data['slug']]) +
                         '?tolocale=fr')
        response = self.client.post(translate_url, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert mock_document_schedule_rendering.called


class PageMoveTests(UserTestCase, WikiTestCase):

    def test_move_conflict(self):
        parent = revision(title='Test page move views',
                          slug='test-page-move-views',
                          is_approved=True,
                          save=True)
        parent_doc = parent.document

        child = revision(title='Child of page-move view test',
                         slug='page-move/test-views',
                         is_approved=True,
                         save=True)
        child_doc = child.document
        child_doc.parent_topic = parent.document
        child_doc.save()

        revision(title='Conflict for page-move view',
                 slug='moved/test-page-move-views/test-views',
                 is_approved=True,
                 save=True)

        data = {'slug': 'moved/test-page-move-views'}
        self.client.login(username='admin', password='testpass')
        with override_flag('page_move', True):
            resp = self.client.post(reverse('wiki.move',
                                            args=(parent_doc.slug,)),
                                    data=data, HTTP_HOST=settings.WIKI_HOST)

        assert resp.status_code == 200
        assert_no_cache_header(resp)
