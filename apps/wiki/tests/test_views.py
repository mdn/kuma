# coding=utf-8

# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import sys
import logging
import datetime
import json
import base64
import time

from urlparse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files import temp as tempfile
from django.db.models import Q
from django.test.client import (Client, FakePayload, encode_multipart,
                                BOUNDARY, CONTENT_TYPE_RE, MULTIPART_CONTENT)
from django.http import Http404
from django.utils.encoding import smart_str

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

import constance.config

from taggit.utils import parse_tags, edit_string_for_tags

from waffle.models import Flag

from sumo.tests import LocalizingClient, post, get
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse

from devmo.tests import override_constance_settings

from . import TestCaseBase, FakeResponse, make_test_file

from authkeys.models import Key

from wiki.content import get_seo_description
from wiki.events import EditDocumentEvent
from wiki.models import (VersionMetadata, Document, Revision, Attachment,
                         DocumentZone,
                         AttachmentRevision, DocumentAttachment, TOC_DEPTH_H4)
from wiki.tests import (doc_rev, document, new_document_data, revision,
                        normalize_html, create_template_test_users,
                        make_translation)
from wiki.views import _version_groups, DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL
from wiki.forms import MIDAIR_COLLISION


class VersionGroupTests(TestCaseBase):
    def test_version_groups(self):
        """Make sure we correctly set up browser/version mappings for the JS"""
        versions = [VersionMetadata(1, 'Firefox 4.0', 'Firefox 4.0', 'fx4',
                                    5.0, False),
                    VersionMetadata(2, 'Firefox 3.5-3.6', 'Firefox 3.5-3.6',
                                    'fx35', 4.0, False),
                    VersionMetadata(4, 'Firefox Mobile 1.1',
                                    'Firefox Mobile 1.1', 'm11', 2.0, False)]
        want = {'fx': [(4.0, '35'), (5.0, '4')],
                'm': [(2.0, '11')]}
        eq_(want, _version_groups(versions))


class RedirectTests(TestCaseBase):
    """Tests for the REDIRECT wiki directive"""

    fixtures = ['test_users.json']

    def test_redirect_suppression(self):
        """The document view shouldn't redirect when passed redirect=no."""
        redirect, _ = doc_rev('REDIRECT <a class="redirect" '
                              'href="http://smoo/">smoo</a>')
        response = self.client.get(
                       redirect.get_absolute_url() + '?redirect=no',
                       follow=True)
        self.assertContains(response, 'REDIRECT ')

    def test_self_redirect_suppression(self):
        """The document view shouldn't redirect to itself."""

        slug = 'redirdoc'
        html = 'REDIRECT <a class="redirect" href="/en-US/docs/' + slug + '">smoo</a>'

        doc = document(title='blah', slug=slug, html=html, save=True,
        locale=settings.WIKI_DEFAULT_LANGUAGE)
        doc.save()
        rev = revision(document=doc, content=html, is_approved=True, save=True)
        rev.save()

        response = self.client.get(doc.get_absolute_url(), follow=True)
        self.assertContains(response, html)


class LocaleRedirectTests(TestCaseBase):
    """Tests for fallbacks to en-US and such for slug lookups."""
    # Some of these may fail or be invalid if your WIKI_DEFAULT_LANGUAGE is de.

    fixtures = ['test_users.json']

    def test_fallback_to_translation(self):
        """If a slug isn't found in the requested locale but is in the default
        locale and if there is a translation of that default-locale document to
        the requested locale, the translation should be served."""
        en_doc, de_doc = self._create_en_and_de_docs()
        response = self.client.get(reverse('wiki.document',
                                           args=(en_doc.slug,),
                                           locale='de'),
                                   follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url())

    def test_fallback_with_query_params(self):
        """The query parameters should be passed along to the redirect."""

        en_doc, de_doc = self._create_en_and_de_docs()
        url = reverse('wiki.document', args=[en_doc.slug], locale='de')
        response = self.client.get(url + '?x=y&x=z', follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url() + '?x=y&x=z')

    def test_redirect_with_no_slug(self):
        """Bug 775241: Fix exception in redirect for URL with ui-locale"""
        loc = settings.WIKI_DEFAULT_LANGUAGE
        url = '/%s/docs/%s/' % (loc, loc)
        try:
            self.client.get(url, follow=True)
        except Http404, e:
            ok_(True)
        except Exception, e:
            ok_(False, "The only exception should be a 404, not this: %s" % e)

    def _create_en_and_de_docs(self):
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_doc = document(locale=en, slug='english-slug')
        en_doc.save()
        de_doc = document(locale='de', parent=en_doc)
        de_doc.save()
        de_rev = revision(document=de_doc, is_approved=True)
        de_rev.save()
        return en_doc, de_doc


class ViewTests(TestCaseBase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    @attr('bug875349')
    def test_json_view(self):
        expected_tags = sorted(['foo', 'bar', 'baz'])
        expected_review_tags = sorted(['tech', 'editorial'])

        doc = Document.objects.get(pk=1)
        doc.save()
        doc.tags.set(*expected_tags)
        doc.current_revision.review_tags.set(*expected_review_tags)

        url = reverse('wiki.json', locale=settings.WIKI_DEFAULT_LANGUAGE)

        resp = self.client.get(url, {'title': 'an article title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('article-title', data['slug'])

        result_tags = sorted([str(x) for x in data['tags']])
        eq_(expected_tags, result_tags)
        
        result_review_tags = sorted([str(x) for x in data['review_tags']])
        eq_(expected_review_tags, result_review_tags)

        url = reverse('wiki.json_slug', args=('article-title',),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        resp = self.client.get(url)
        ok_('Access-Control-Allow-Origin' in resp)
        eq_('*', resp['Access-Control-Allow-Origin'])
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('an article title', data['title'])
        ok_('translations' in data)

        result_tags = sorted([str(x) for x in data['tags']])
        eq_(expected_tags, result_tags)
        
        result_review_tags = sorted([str(x) for x in data['review_tags']])
        eq_(expected_review_tags, result_review_tags)

    def test_history_view(self):
        slug = 'history-view-test-doc'
        html = 'history view test doc'

        doc = document(title='History view test doc', slug=slug,
                       html=html, save=True,
                       locale=settings.WIKI_DEFAULT_LANGUAGE)

        for i in xrange(1, 51):
            rev = revision(document=doc, content=html,
                           comment='Revision %s' % i,
                           is_approved=True, save=True)
            rev.save()

        url = reverse('wiki.document_revisions', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)

        resp = self.client.get(url)
        eq_(200, resp.status_code)

        all_url = urlparams(reverse('wiki.document_revisions', args=(slug,),
                                    locale=settings.WIKI_DEFAULT_LANGUAGE),
                            limit='all')
        resp = self.client.get(url)
        eq_(200, resp.status_code)

    def test_toc_view(self):
        slug = 'toc_test_doc'
        html = '<h2>Head 2</h2><h3>Head 3</h3>'

        doc = document(title='blah', slug=slug, html=html, save=True,
                       locale=settings.WIKI_DEFAULT_LANGUAGE)
        doc.save()
        rev = revision(document=doc, content=html, is_approved=True, save=True)
        rev.save()

        url = reverse('wiki.toc', args=[slug],
                      locale=settings.WIKI_DEFAULT_LANGUAGE)

        resp = self.client.get(url)
        ok_('Access-Control-Allow-Origin' in resp)
        eq_('*', resp['Access-Control-Allow-Origin'])
        eq_(resp.content, '<ol><li><a href="#Head_2" rel="internal">Head 2</a>'
                          '<ol><li><a href="#Head_3" rel="internal">Head 3</a>'
                          '</ol></li></ol>')

    @attr('bug875349')
    def test_children_view(self):
        test_content = '<p>Test <a href="http://example.com">Summary</a></p>'

        def _make_doc(title, slug, parent=None, is_redir=False):
            doc = document(title=title,
                           slug=slug,
                           save=True,
                           is_redirect=is_redir)
            if is_redir:
                content = 'REDIRECT <a class="redirect" href="x">Blah</a>'
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
        grandchild_doc_1 = _make_doc('Grandchild 1',
            'Root/Child_1/Grandchild_1', child_doc_1)
        grandchild_doc_2 = _make_doc('Grandchild 2',
            'Root/Child_1/Grandchild_2', child_doc_1)
        great_grandchild_doc_1 = _make_doc('Great Grandchild 1',
            'Root/Child_1/Grandchild_2/Great_Grand_Child_1', grandchild_doc_2)
        child_doc_2 = _make_doc('Child 2', 'Root/Child_2', root_doc)
        child_doc_3 = _make_doc('Child 3', 'Root/Child_3', root_doc, True)

        for expand in (True, False):
            url = reverse('wiki.get_children', args=['Root'],
                          locale=settings.WIKI_DEFAULT_LANGUAGE)
            if expand:
                url = '%s?expand' % url
            resp = self.client.get(url)
            ok_('Access-Control-Allow-Origin' in resp)
            eq_('*', resp['Access-Control-Allow-Origin'])
            json_obj = json.loads(resp.content)

            # Basic structure creation testing
            eq_(json_obj['slug'], 'Root')
            if not expand:
                ok_('summary' not in json_obj)
            else:
                eq_(json_obj['summary'],
                    'Test <a href="http://example.com">Summary</a>')
                ok_('tags' in json_obj)
                ok_('review_tags' in json_obj)
            eq_(len(json_obj['subpages']), 2)
            eq_(len(json_obj['subpages'][0]['subpages']), 2)
            eq_(json_obj['subpages'][0]['subpages'][1]['title'], 'Grandchild 2')

        # Depth parameter testing
        def _depth_test(depth, aught):
            url = reverse('wiki.get_children', args=['Root'],
                locale=settings.WIKI_DEFAULT_LANGUAGE) + '?depth=' + str(depth)
            resp = self.client.get(url)
            json_obj = json.loads(resp.content)
            eq_(len(json_obj['subpages'][0]['subpages'][1]['subpages']), aught)

        _depth_test(2, 0)
        _depth_test(3, 1)
        _depth_test(6, 1)

        # Sorting test
        sort_root_doc = _make_doc('Sort Root', 'Sort_Root')
        sort_child_doc_1 = _make_doc('B Child', 'Sort_Root/B_Child',
                                     sort_root_doc)
        sort_child_doc_2 = _make_doc('A Child', 'Sort_Root/A_Child',
                                     sort_root_doc)
        resp = self.client.get(reverse('wiki.get_children', args=['Sort_Root'],
            locale=settings.WIKI_DEFAULT_LANGUAGE))
        json_obj = json.loads(resp.content)
        eq_(json_obj['subpages'][0]['title'], 'A Child')

    def test_summary_view(self):
        """The ?summary option should restrict document view to summary"""
        d, r = doc_rev("""
            <p>Foo bar <a href="http://example.com">baz</a></p>
            <p>Quux xyzzy</p>
        """)
        resp = self.client.get('%s?raw&summary' % d.get_absolute_url())
        eq_(resp.content, 'Foo bar <a href="http://example.com">baz</a>')

    def test_revision_view_bleached_content(self):
        """Bug 821988: Revision content should be cleaned with bleach"""
        d, r = doc_rev("""
            <a href="#" onload=alert(3)>Hahaha</a>
            <svg><svg onload=alert(3);>
        """)
        resp = self.client.get(r.get_absolute_url())
        page = pq(resp.content)
        ct = page.find('#doc-content .page-content').html()
        ok_('<svg>' not in ct)
        ok_('<a href="#">Hahaha</a>' in ct)


class PermissionTests(TestCaseBase):

    fixtures = ['test_users.json']

    def setUp(self):
        """Set up the permissions, groups, and users needed for the tests"""
        super(PermissionTests, self).setUp()
        (self.perms, self.groups, self.users, self.superuser) = (
            create_template_test_users())

    def test_template_permissions(self):
        msg = ('edit', 'create')

        for is_add in (True, False):

            slug_trials = (
                ('test_for_%s', (
                    (True, self.superuser),
                    (True, self.users['none']),
                    (True, self.users['all']),
                    (True, self.users['add']),
                    (True, self.users['change']),
                )),
                ('Template:test_for_%s', (
                    (True,       self.superuser),
                    (False,      self.users['none']),
                    (True,       self.users['all']),
                    (is_add,     self.users['add']),
                    (not is_add, self.users['change']),
                ))
            )

            for slug_tmpl, trials in slug_trials:
                for expected, user in trials:

                    username = user.username
                    slug = slug_tmpl % username
                    locale = settings.WIKI_DEFAULT_LANGUAGE

                    Document.objects.all().filter(slug=slug).delete()
                    if not is_add:
                        doc = document(save=True, slug=slug, title=slug,
                                       locale=locale)
                        revision(save=True, document=doc)

                    self.client.login(username=username, password='testpass')

                    data = new_document_data()
                    slug = slug_tmpl % username
                    data.update({"title": slug, "slug": slug})

                    if is_add:
                        url = reverse('wiki.new_document', locale=locale)
                        resp = self.client.post(url, data, follow=False)
                    else:
                        data['form'] = 'rev'
                        url = reverse('wiki.edit_document', args=(slug,),
                                      locale=locale)
                        resp = self.client.post(url, data, follow=False)

                    if expected:
                        eq_(302, resp.status_code,
                            "%s should be able to %s %s" %
                            (user, msg[is_add], slug))
                        Document.objects.filter(slug=slug).delete()
                    else:
                        eq_(403, resp.status_code,
                            "%s should not be able to %s %s" %
                            (user, msg[is_add], slug))


class ConditionalGetTests(TestCaseBase):
    """Tests for conditional GET on document view"""
    fixtures = ['test_users.json']

    def test_last_modified(self):
        """Ensure the last-modified stamp of a document is cached"""

        self.d, self.r = doc_rev()
        self.url = reverse('wiki.document',
                           args=[self.d.slug],
                           locale=settings.WIKI_DEFAULT_LANGUAGE)

        # There should be no last-modified date cached for this document yet.
        cache_key = (DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL %
                     self.d.natural_cache_key)
        ok_(not cache.get(cache_key))

        # Now, try a request, and ensure that the last-modified header is
        # present.
        response = self.client.get(self.url, follow=False)
        ok_(response.has_header('last-modified'))
        last_mod = response['last-modified']

        # Try another request, using If-Modified-Since. THis should be a 304
        response = self.client.get(self.url, follow=False,
                                   HTTP_IF_MODIFIED_SINCE=last_mod)
        eq_(304, response.status_code)

        # Finally, ensure that the last-modified was cached.
        cached_last_mod = cache.get(cache_key)
        eq_(self.d.modified.strftime('%s'), cached_last_mod)

        # Let the clock tick, so the last-modified will change on edit.
        time.sleep(1.0)

        # Edit the document, ensure the last-modified has been invalidated.
        revision(document=self.d, content="New edits", save=True)
        ok_(not cache.get(cache_key))

        # This should be another 304, but the last-modified in response and
        # cache should have changed.
        response = self.client.get(self.url, follow=False,
                                   HTTP_IF_MODIFIED_SINCE=last_mod)
        eq_(200, response.status_code)
        ok_(last_mod != response['last-modified'])
        ok_(cached_last_mod != cache.get(cache_key))


class ReadOnlyTests(TestCaseBase):
    """Tests readonly scenarios"""
    fixtures = ['test_users.json', 'wiki/documents.json']

    def setUp(self):
        super(ReadOnlyTests, self).setUp()
        self.d, self.r = doc_rev()
        self.edit_url = reverse('wiki.edit_document', args=[self.d.full_path])

    def test_everyone(self):
        """ kumaediting: everyone, kumabanned: none  """
        self.kumaediting_flag.everyone = True
        self.kumaediting_flag.save()

        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(200, resp.status_code)

    def test_superusers_only(self):
        """ kumaediting: superusers, kumabanned: none """
        self.kumaediting_flag.everyone = None
        self.kumaediting_flag.superusers = True
        self.kumaediting_flag.save()

        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(403, resp.status_code)
        ok_('The wiki is in read-only mode.' in resp.content)
        self.client.logout()

        self.client.login(username='admin', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(200, resp.status_code)

    def test_banned_users(self):
        """ kumaediting: everyone, kumabanned: testuser2 """
        self.kumaediting_flag.everyone = True
        self.kumaediting_flag.save()
        # ban testuser2
        kumabanned = Flag.objects.create(name='kumabanned')
        kumabanned.users = User.objects.filter(username='testuser2')
        kumabanned.save()

        # testuser can still access
        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(200, resp.status_code)
        self.client.logout()

        # testuser2 cannot
        self.client.login(username='testuser2', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(403, resp.status_code)
        ok_('Your account has been banned from making edits.' in resp.content)

        # ban testuser01 and testuser2
        kumabanned.users = User.objects.filter(Q(username='testuser2') |
                                               Q(username='testuser01'))
        kumabanned.save()

        # testuser can still access
        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(200, resp.status_code)
        self.client.logout()

        # testuser2 cannot access
        self.client.login(username='testuser2', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(403, resp.status_code)
        ok_('Your account has been banned from making edits.' in resp.content)

        # testuser01 cannot access
        self.client.login(username='testuser01', password='testpass')
        resp = self.client.get(self.edit_url)
        eq_(403, resp.status_code)
        ok_('Your account has been banned from making edits.' in resp.content)


class KumascriptIntegrationTests(TestCaseBase):
    """Tests for usage of the kumascript service.

    Note that these tests really just check whether or not the service was
    used, and are not integration tests meant to exercise the real service.
    """

    fixtures = ['test_users.json']

    def setUp(self):
        super(KumascriptIntegrationTests, self).setUp()

        self.d, self.r = doc_rev()
        self.r.content = "TEST CONTENT"
        self.r.save()
        self.d.tags.set('foo', 'bar', 'baz')
        self.url = reverse('wiki.document',
                           args=(self.d.slug,),
                           locale=self.d.locale)

        # NOTE: We could do this instead of using the @patch decorator over and
        # over, but it requires an upgrade of mock to 0.8.0

        # self.mock_kumascript_get = (
        #         mock.patch('wiki.kumascript.get'))
        # self.mock_kumascript_get.return_value = self.d.html

    def tearDown(self):
        super(KumascriptIntegrationTests, self).tearDown()

        # NOTE: We could do this instead of using the @patch decorator over and
        # over, but it requires an upgrade of mock to 0.8.0

        # self.mock_kumascript_get.stop()

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('wiki.kumascript.get')
    def test_basic_view(self, mock_kumascript_get):
        """When kumascript timeout is non-zero, the service should be used"""
        mock_kumascript_get.return_value = (self.d.html, None)
        self.client.get(self.url, follow=False)
        ok_(mock_kumascript_get.called,
            "kumascript should have been used")

    @override_constance_settings(KUMASCRIPT_TIMEOUT=0.0)
    @mock.patch('wiki.kumascript.get')
    def test_disabled(self, mock_kumascript_get):
        """When disabled, the kumascript service should not be used"""
        mock_kumascript_get.return_value = (self.d.html, None)
        self.client.get(self.url, follow=False)
        ok_(not mock_kumascript_get.called,
            "kumascript not should have been used")

    @override_constance_settings(KUMASCRIPT_TIMEOUT=0.0)
    @mock.patch('wiki.kumascript.get')
    def test_disabled_rendering(self, mock_kumascript_get):
        """When disabled, the kumascript service should not be used
        in rendering"""
        mock_kumascript_get.return_value = (self.d.html, None)
        settings.CELERY_ALWAYS_EAGER = True
        self.d.schedule_rendering('max-age=0')
        ok_(not mock_kumascript_get.called,
            "kumascript not should have been used")

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('wiki.kumascript.get')
    def test_nomacros(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.d.html, None)
        self.client.get('%s?nomacros' % self.url, follow=False)
        ok_(not mock_kumascript_get.called,
            "kumascript should not have been used")

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('wiki.kumascript.get')
    def test_raw(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.d.html, None)
        self.client.get('%s?raw' % self.url, follow=False)
        ok_(not mock_kumascript_get.called,
            "kumascript should not have been used")

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('wiki.kumascript.get')
    def test_raw_macros(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.d.html, None)
        self.client.get('%s?raw&macros' % self.url, follow=False)
        ok_(mock_kumascript_get.called,
            "kumascript should have been used")

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0,
                                 KUMASCRIPT_MAX_AGE=1234)
    @mock.patch('requests.get')
    def test_ua_max_age_zero(self, mock_requests_get):
        """Authenticated users can request a zero max-age for kumascript"""
        trap = {}

        def my_requests_get(url, headers=None, timeout=None):
            trap['headers'] = headers
            return FakeResponse(status_code=200,
                headers={}, text='HELLO WORLD')

        mock_requests_get.side_effect = my_requests_get

        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('max-age=1234', trap['headers']['Cache-Control'])

        self.client.login(username='admin', password='testpass')
        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('no-cache', trap['headers']['Cache-Control'])

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0,
                                 KUMASCRIPT_MAX_AGE=1234)
    @mock.patch('requests.get')
    def test_ua_no_cache(self, mock_requests_get):
        """Authenticated users can request no-cache for kumascript"""
        trap = {}

        def my_requests_get(url, headers=None, timeout=None):
            trap['headers'] = headers
            return FakeResponse(status_code=200,
                headers={}, text='HELLO WORLD')

        mock_requests_get.side_effect = my_requests_get

        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('max-age=1234', trap['headers']['Cache-Control'])

        self.client.login(username='admin', password='testpass')
        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('no-cache', trap['headers']['Cache-Control'])

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0,
                                 KUMASCRIPT_MAX_AGE=1234)
    @mock.patch('requests.get')
    def test_conditional_get(self, mock_requests_get):
        """Ensure conditional GET in requests to kumascript work as expected"""
        expected_etag = "8675309JENNY"
        expected_modified = "Wed, 14 Mar 2012 22:29:17 GMT"
        expected_content = "HELLO THERE, WORLD"

        trap = dict(req_cnt=0)

        def my_requests_get(url, headers=None, timeout=None):
            trap['req_cnt'] += 1
            trap['headers'] = headers
            if trap['req_cnt'] in [1, 2]:
                return FakeResponse(status_code=200, text=expected_content,
                    headers={
                        "etag": expected_etag,
                        "last-modified": expected_modified,
                        "age": 456
                    })
            else:
                return FakeResponse(status_code=304, text='',
                    headers={
                        "etag": expected_etag,
                        "last-modified": expected_modified,
                        "age": 123
                    })

        mock_requests_get.side_effect = my_requests_get

        # First request to let the view cache etag / last-modified
        response = self.client.get(self.url)

        # Clear rendered_html to force another request.
        self.d.rendered_html = ''
        self.d.save()

        # Second request to verify the view sends them back
        response = self.client.get(self.url)
        eq_(expected_etag, trap['headers']['If-None-Match'])
        eq_(expected_modified, trap['headers']['If-Modified-Since'])

        # Third request to verify content was cached and served on a 304
        response = self.client.get(self.url)
        ok_(expected_content in response.content)

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0,
                                 KUMASCRIPT_MAX_AGE=600)
    @mock.patch('requests.get')
    def test_error_reporting(self, mock_requests_get):
        """Kumascript reports errors in HTTP headers, Kuma should display"""

        # Make sure we have enough log messages to ensure there are more than
        # 10 lines of Base64 in headers. This ensures that there'll be a
        # failure if the view sorts FireLogger sequence number alphabetically
        # instead of numerically.
        expected_errors = {
            "logs": [
                {"level": "debug",
                  "message": "Message #1",
                  "args": ['TestError'],
                  "time": "12:32:03 GMT-0400 (EDT)",
                  "timestamp": "1331829123101000"},
                {"level": "warning",
                  "message": "Message #2",
                  "args": ['TestError'],
                  "time": "12:33:58 GMT-0400 (EDT)",
                  "timestamp": "1331829238052000"},
                {"level": "info",
                  "message": "Message #3",
                  "args": ['TestError'],
                  "time": "12:34:22 GMT-0400 (EDT)",
                  "timestamp": "1331829262403000"},
                {"level": "debug",
                  "message": "Message #4",
                  "time": "12:32:03 GMT-0400 (EDT)",
                  "timestamp": "1331829123101000"},
                {"level": "warning",
                  "message": "Message #5",
                  "time": "12:33:58 GMT-0400 (EDT)",
                  "timestamp": "1331829238052000"},
                {"level": "info",
                  "message": "Message #6",
                  "time": "12:34:22 GMT-0400 (EDT)",
                  "timestamp": "1331829262403000"},
            ]
        }

        # Pack it up, get ready to ship it out.
        d_json = json.dumps(expected_errors)
        d_b64 = base64.encodestring(d_json)
        d_lines = [x for x in d_b64.split("\n") if x]

        # Headers are case-insensitive, so let's just drive that point home
        p = ['firelogger', 'FIRELOGGER', 'FireLogger']
        fl_uid = 8675309
        headers_out = {}
        for i in range(0, len(d_lines)):
            headers_out['%s-%s-%s' % (p[i % len(p)], fl_uid, i)] = d_lines[i]

        # Now, trap the request from the view.
        trap = {}

        def my_requests_get(url, headers=None, timeout=None):
            trap['headers'] = headers
            return FakeResponse(
                status_code=200,
                text='HELLO WORLD',
                headers=headers_out
            )
        mock_requests_get.side_effect = my_requests_get

        # Finally, fire off the request to the view and ensure that the log
        # messages were received and displayed on the page. But, only for a
        # logged in user.
        self.client.login(username='admin', password='testpass')
        response = self.client.get(self.url)
        eq_(trap['headers']['X-FireLogger'], '1.2')
        for error in expected_errors['logs']:
            ok_(error['message'] in response.content)

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0,
                                 KUMASCRIPT_MAX_AGE=600)
    @mock.patch('requests.post')
    def test_preview_nonascii(self, mock_post):
        """POSTing non-ascii to kumascript should encode to utf8"""
        content = u'Français'
        trap = {}

        def my_post(url, timeout=None, headers=None, data=None):
            trap['data'] = data
            return FakeResponse(status_code=200, headers={},
                                text=content.encode('utf8'))
        mock_post.side_effect = my_post

        self.client.login(username='admin', password='testpass')
        self.client.post(reverse('wiki.preview'), {'content': content})
        try:
            trap['data'].decode('utf8')
        except UnicodeDecodeError:
            ok_(False, "Data wasn't posted as utf8")


class DocumentSEOTests(TestCaseBase):
    """Tests for the document seo logic"""

    fixtures = ['test_users.json']

    def test_seo_title(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # Utility to make a quick doc
        def _make_doc(title, aught_titles, slug):
            doc = document(save=True, slug=slug, title=title,
                                       locale=settings.WIKI_DEFAULT_LANGUAGE)
            revision(save=True, document=doc)
            response = client.get(reverse('wiki.document', args=[slug],
                                    locale=settings.WIKI_DEFAULT_LANGUAGE))
            page = pq(response.content)

            ok_(page.find('title').text() in aught_titles)

        # Test nested document titles
        _make_doc('One', ['One | MDN'], 'one')
        _make_doc('Two', ['Two - One | MDN'], 'one/two')
        _make_doc('Three', ['Three - One | MDN'], 'one/two/three')
        _make_doc(u'Special Φ Char', [u'Special \u03a6 Char - One | MDN',
                                      u'Special \xce\xa6 Char - One | MDN'],
                  'one/two/special_char')

        # Additional tests for /Web/*  changes
        _make_doc('Firefox OS', ['Firefox OS | MDN'], 'firefox_os')
        _make_doc('Email App', ['Email App - Firefox OS | MDN'], 'firefox_os/email_app')
        _make_doc('Web', ['Web | MDN'], 'Web')
        _make_doc('HTML', ['HTML | MDN'], 'Web/html')
        _make_doc('Fieldset', ['Fieldset - HTML | MDN'], 'Web/html/fieldset')
        _make_doc('Legend', ['Legend - HTML | MDN'], 'Web/html/fieldset/legend')


    def test_seo_script(self):

        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        def make_page_and_compare_seo(slug, content, aught_preview):
            # Create the doc
            data = new_document_data()
            data.update({'title': 'blah', 'slug': slug, 'content': content})
            response = client.post(reverse('wiki.new_document',
                                       locale=settings.WIKI_DEFAULT_LANGUAGE),
                                   data)
            eq_(302, response.status_code)

            # Connect to newly created page
            response = self.client.get(reverse('wiki.document', args=[slug],
                                       locale=settings.WIKI_DEFAULT_LANGUAGE))
            page = pq(response.content)
            meta_content = page.find('meta[name=description]').attr('content')
            eq_(str(meta_content).decode('utf-8'),
                str(aught_preview).decode('utf-8'))

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
          'I am awesome. A link is also cool')


class DocumentEditingTests(TestCaseBase):
    """Tests for the document-editing view"""

    fixtures = ['test_users.json']

    def test_noindex_post(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # Go to new document page to ensure no-index header works
        response = client.get(reverse('wiki.new_document', args=[],
                                       locale=settings.WIKI_DEFAULT_LANGUAGE))
        eq_(response['X-Robots-Tag'], 'noindex')

    @attr('bug821986')
    def test_editor_safety_filter(self):
        """Safety filter should be applied before rendering editor"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        r = revision(save=True, content="""
            <svg><circle onload=confirm(3)>
        """)

        args = [r.document.full_path]
        urls = (
            reverse('wiki.edit_document', args=args),
            '%s?tolocale=%s' % (reverse('wiki.translate', args=args), 'fr')
        )
        for url in urls:
            page = pq(client.get(url).content)
            editor_src = page.find('#id_content').text()
            ok_('onload' not in editor_src)

    def test_create_on_404(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # Create the parent page.
        d, r = doc_rev()

        # Establish attribs of child page.
        locale = settings.WIKI_DEFAULT_LANGUAGE
        local_slug = 'Some_New_Title'
        slug = '%s/%s' % (d.slug, local_slug)
        url = reverse('wiki.document', args=[slug], locale=locale)

        # Ensure redirect to create new page on attempt to visit non-existent
        # child page.
        resp = client.get(url)
        eq_(302, resp.status_code)
        ok_('docs/new' in resp['Location'])
        ok_('?slug=%s' % local_slug  in resp['Location'])

        # Ensure real 404 for visit to non-existent page with params common to
        # kumascript and raw content API.
        for p_name in ('raw', 'include', 'nocreate'):
            sub_url = '%s?%s=1' % (url, p_name)
            resp = client.get(sub_url)
            eq_(404, resp.status_code)

        # Ensure root level documents work, not just children
        response = client.get(reverse('wiki.document',
                                      args=['noExist'], locale=locale))
        eq_(302, response.status_code)

        response = client.get(reverse('wiki.document',
                                      args=['Template:NoExist'],
                                      locale=locale))
        eq_(302, response.status_code)
    
    def test_new_document_comment(self):
        """ Creating a new document with a revision comment saves the comment """
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        
        comment = 'I am the revision comment'
        slug = 'Test-doc-comment'
        loc = settings.WIKI_DEFAULT_LANGUAGE

        # Create a new doc.
        data = new_document_data()
        data.update({'slug': slug, 'comment': comment})
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(comment,
            Document.objects.get(slug=slug, locale=loc).current_revision.comment)

    @attr('toc')
    def test_toc_initial(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        resp = client.get(reverse('wiki.new_document'))
        eq_(200, resp.status_code)

        page = pq(resp.content)
        toc_select = page.find('#id_toc_depth')
        toc_options = toc_select.find('option')
        for option in toc_options:
            opt_element = pq(option)
            found_selected = False
            if opt_element.attr('selected'):
                found_selected = True
                eq_(str(TOC_DEPTH_H4), opt_element.attr('value'))
        if not found_selected:
            raise AssertionError("No ToC depth initially selected.")

    @attr('retitle')
    def test_retitling_solo_doc(self):
        """ Editing just title of non-parent doc:
            * Changes title
            * Doesn't cause errors
            * Doesn't create redirect
        """
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        new_title = 'Some New Title'
        d, r = doc_rev()
        old_title = d.title
        data = new_document_data()
        data.update({'title': new_title,
                     'form': 'rev'})
        data['slug'] = ''
        url = reverse('wiki.edit_document', args=[d.full_path])
        client.post(url, data)
        eq_(new_title,
            Document.objects.get(slug=d.slug, locale=d.locale).title)
        try:
            Document.objects.get(title=old_title)
            self.fail("Should not find doc by old title after retitling.")
        except Document.DoesNotExist:
            pass

    @attr('retitle')
    def test_retitling_parent_doc(self):
        """ Editing just title of parent doc:
            * Changes title
            * Doesn't cause errors
            * Doesn't create redirect
        """
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # create parent doc & rev along with child doc & rev
        d = document(title='parent', save=True)
        revision(document=d, content='parent', save=True)
        d2 = document(title='child', parent_topic=d, save=True)
        revision(document=d2, content='child', save=True)

        old_title = d.title
        new_title = 'Some New Title'
        data = new_document_data()
        data.update({'title': new_title,
                     'form': 'rev'})
        data['slug'] = ''
        url = reverse('wiki.edit_document', args=[d.full_path])
        client.post(url, data)
        eq_(new_title,
            Document.objects.get(slug=d.slug, locale=d.locale).title)
        try:
            Document.objects.get(title=old_title)
            self.fail("Should not find doc by old title after retitling.")
        except Document.DoesNotExist:
            pass

    def test_slug_change_ignored_for_iframe(self):
        """When the title of an article is edited in an iframe, the change is
        ignored."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        new_slug = 'some_new_slug'
        d, r = doc_rev()
        old_slug = d.slug
        data = new_document_data()
        data.update({'title': d.title,
                     'slug': new_slug,
                     'form': 'rev'})
        client.post('%s?iframe=1' % reverse('wiki.edit_document',
                                            args=[d.full_path]), data)
        eq_(old_slug, Document.objects.get(slug=d.slug,
                                             locale=d.locale).slug)
        assert "REDIRECT" not in Document.objects.get(slug=old_slug).html

    @attr('clobber')
    def test_slug_collision_errors(self):
        """When an attempt is made to retitle an article and another with that
        title already exists, there should be form errors"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        exist_slug = "existing-doc"

        # Create a new doc.
        data = new_document_data()
        data.update({"slug": exist_slug})
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)

        # Create another new doc.
        data = new_document_data()
        data.update({"slug": 'some-new-title'})
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)

        # Now, post an update with duplicate slug
        data.update({
            'form': 'rev',
            'slug': exist_slug
        })
        resp = client.post(reverse('wiki.edit_document',
                                   args=['some-new-title']),
                           data)
        eq_(200, resp.status_code)
        p = pq(resp.content)

        ok_(p.find('.errorlist').length > 0)
        ok_(p.find('.errorlist a[href="#id_slug"]').length > 0)

    @attr('clobber')
    def test_redirect_can_be_clobbered(self):
        """When an attempt is made to retitle an article, and another article
        with that title exists but is a redirect, there should be no errors and
        the redirect should be replaced."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        exist_title = "Existing doc"
        exist_slug = "existing-doc"

        changed_title = 'Changed title'
        changed_slug = 'changed-title'

        # Create a new doc.
        data = new_document_data()
        data.update({"title": exist_title, "slug": exist_slug})
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)

        # Change title and slug
        data.update({'form': 'rev',
                     'title': changed_title,
                     'slug': changed_slug})
        resp = client.post(reverse('wiki.edit_document',
                                    args=[exist_slug]),
                           data)
        eq_(302, resp.status_code)

        # Change title and slug back to originals, clobbering the redirect
        data.update({'form': 'rev',
                     'title': exist_title,
                     'slug': exist_slug})
        resp = client.post(reverse('wiki.edit_document',
                                    args=[changed_slug]),
                           data)
        eq_(302, resp.status_code)

    def test_changing_metadata(self):
        """Changing metadata works as expected."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev()
        data = new_document_data()
        data.update({'firefox_versions': [1, 2, 3],
                     'operating_systems': [1, 3],
                     'form': 'doc'})
        client.post(reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(3, d.firefox_versions.count())
        eq_(2, d.operating_systems.count())
        data.update({'firefox_versions': [1, 2],
                     'operating_systems': [2],
                     'form': 'doc'})
        client.post(reverse('wiki.edit_document', args=[data['slug']]), data)
        eq_(2, d.firefox_versions.count())
        eq_(1, d.operating_systems.count())

    def test_invalid_slug(self):
        """Slugs cannot contain "$", but can contain "/"."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        data = new_document_data()

        data['title'] = 'valid slug'
        data['slug'] = 'valid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertRedirects(response,
                reverse('wiki.document', args=[data['slug']],
                                     locale=settings.WIKI_DEFAULT_LANGUAGE))

        # Slashes should not be acceptable via form input
        data['title'] = 'valid with slash'
        data['slug'] = 'va/lid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, 'The slug provided is not valid.')

        # Dollar sign is reserved for verbs
        data['title'] = 'invalid with dollars'
        data['slug'] = 'inva$lid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, 'The slug provided is not valid.')

        # Question mark is reserved for query params
        data['title'] = 'invalid with questions'
        data['slug'] = 'inva?lid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, 'The slug provided is not valid.')

    def test_invalid_reserved_term_slug(self):
        """Slugs should not collide with reserved URL patterns"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        data = new_document_data()

        # TODO: This is info derived from urls.py, but unsure how to DRY it
        reserved_slugs = (
            'ckeditor_config.js',
            'watch-ready-for-review',
            'unwatch-ready-for-review',
            'watch-approved',
            'unwatch-approved',
            '.json',
            'new',
            'all',
            'preview-wiki-content',
            'category/10',
            'needs-review/technical',
            'needs-review/',
            'feeds/atom/all/',
            'feeds/atom/needs-review/technical',
            'feeds/atom/needs-review/',
            'tag/tasty-pie'
        )

        for term in reserved_slugs:
            data['title'] = 'invalid with %s' % term
            data['slug'] = term
            response = client.post(reverse('wiki.new_document'), data)
            self.assertContains(response, 'The slug provided is not valid.')

    def test_slug_revamp(self):

        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        def _createAndRunTests(slug):

            # Create some vars
            locale = settings.WIKI_DEFAULT_LANGUAGE
            foreign_locale = 'es'
            new_doc_url = reverse('wiki.new_document')
            invalid_slug = invalid_slug1 = "some/thing"
            invalid_slug2 = "some?thing"
            invalid_slug3 = "some thing"
            child_slug = 'kiddy'
            grandchild_slug = 'grandkiddy'

            # Create the document data
            doc_data = new_document_data()
            doc_data['title'] = slug + ' Doc'
            doc_data['slug'] = slug
            doc_data['content'] = 'This is the content'
            doc_data['is_localizable'] = True

            """ NEW DOCUMENT CREATION, CHILD CREATION """

            # Create the document, validate it exists
            response = client.post(new_doc_url, doc_data)
            eq_(302, response.status_code)  # 302 = good, forward to new page
            ok_(slug in response['Location'])
            self.assertRedirects(response, reverse('wiki.document',
                                                   locale=locale, args=[slug]))
            eq_(client.get(reverse('wiki.document',
                                   locale=locale,
                                   args=[slug])
                          ).status_code, 200)
            doc = Document.objects.get(locale=locale, slug=slug)
            eq_(doc.slug, slug)
            eq_(0, len(Document.objects.filter(title=doc_data['title']
                                               + 'Redirect')))

            # Create child document data
            child_data = new_document_data()
            child_data['title'] = slug + ' Child Doc'
            child_data['slug'] = invalid_slug
            child_data['content'] = 'This is the content'
            child_data['is_localizable'] = True

            # Attempt to create the child with invalid slug, validate it fails
            def test_invalid_slug(inv_slug, url, data, doc):
                data['slug'] = inv_slug
                response = client.post(url, data)
                page = pq(response.content)
                eq_(200, response.status_code)  # 200 = bad, invalid data
                # Slug doesn't add parent
                eq_(inv_slug, page.find('input[name=slug]')[0].value)
                eq_(doc.get_absolute_url(),
                    page.find('.metadataDisplay').attr('href'))
                self.assertContains(response,
                                    'The slug provided is not valid.')

            test_invalid_slug(invalid_slug1,
                              new_doc_url + '?parent=' + str(doc.id),
                              child_data, doc)
            test_invalid_slug(invalid_slug2,
                              new_doc_url + '?parent=' + str(doc.id),
                              child_data, doc)
            test_invalid_slug(invalid_slug3,
                              new_doc_url + '?parent=' + str(doc.id),
                              child_data, doc)

            # Attempt to create the child with *valid* slug,
            # should succeed and redirect
            child_data['slug'] = child_slug
            full_child_slug = slug + '/' + child_data['slug']
            response = client.post(new_doc_url + '?parent=' + str(doc.id),
                                   child_data)
            eq_(302, response.status_code)
            self.assertRedirects(response, reverse('wiki.document',
                                                   locale=locale,
                                                   args=[full_child_slug]))
            child_doc = Document.objects.get(locale=locale,
                                             slug=full_child_slug)
            eq_(child_doc.slug, full_child_slug)
            eq_(0, len(Document.objects.filter(
                title=child_data['title'] + ' Redirect 1',
                locale=locale)))

            # Create grandchild data
            grandchild_data = new_document_data()
            grandchild_data['title'] = slug + ' Grandchild Doc'
            grandchild_data['slug'] = invalid_slug
            grandchild_data['content'] = 'This is the content'
            grandchild_data['is_localizable'] = True

            # Attempt to create the child with invalid slug, validate it fails
            response = client.post(
                new_doc_url + '?parent=' + str(child_doc.id), grandchild_data)
            page = pq(response.content)
            eq_(200, response.status_code)  # 200 = bad, invalid data
            # Slug doesn't add parent
            eq_(invalid_slug, page.find('input[name=slug]')[0].value)
            eq_(child_doc.get_absolute_url(),
                page.find('.metadataDisplay').attr('href'))
            self.assertContains(response, 'The slug provided is not valid.')

            # Attempt to create the child with *valid* slug,
            # should succeed and redirect
            grandchild_data['slug'] = grandchild_slug
            full_grandchild_slug = (full_child_slug
                                    + '/' + grandchild_data['slug'])
            response = client.post(new_doc_url
                                    + '?parent=' + str(child_doc.id),
                                   grandchild_data)
            eq_(302, response.status_code)
            self.assertRedirects(response,
                                 reverse('wiki.document', locale=locale,
                                         args=[full_grandchild_slug]))
            grandchild_doc = Document.objects.get(locale=locale,
                                                  slug=full_grandchild_slug)
            eq_(grandchild_doc.slug, full_grandchild_slug)
            eq_(0, len(Document.objects.filter(
                                title=grandchild_data['title'] + ' Redirect 1',
                                locale=locale)))

            """ EDIT DOCUMENT TESTING """
            def _run_edit_tests(edit_slug, edit_data, edit_doc,
                                edit_parent_path):
                # Load "Edit" page for the root doc, ensure no "/" in the slug
                # Also ensure the 'parent' link is not present
                response = client.get(reverse('wiki.edit_document',
                                          args=[edit_doc.slug], locale=locale))
                eq_(200, response.status_code)
                page = pq(response.content)
                eq_(edit_data['slug'], page.find('input[name=slug]')[0].value)
                eq_(edit_parent_path,
                    page.find('.metadataDisplay').attr('href'))

                # Attempt an invalid edit of the root,
                # ensure the slug stays the same (i.e. no parent prepending)
                def test_invalid_slug_edit(inv_slug, url, data):
                    data['slug'] = inv_slug
                    data['form'] = 'rev'
                    response = client.post(url, data)
                    eq_(200, response.status_code)  # 200 = bad, invalid data
                    page = pq(response.content)
                    # Slug doesn't add parent
                    eq_(inv_slug, page.find('input[name=slug]')[0].value)
                    eq_(edit_parent_path,
                        page.find('.metadataDisplay').attr('href'))
                    self.assertContains(response,
                                        'The slug provided is not valid.')
                    # Ensure no redirect
                    eq_(0, len(Document.objects.filter(
                                        title=data['title'] + ' Redirect 1',
                                        locale=locale)))

                edit_bad_url = reverse('wiki.edit_document',
                                       args=[edit_doc.slug], locale=locale)

                # Push a valid edit, without changing the slug
                edit_data['slug'] = edit_slug
                edit_data['form'] = 'rev'
                response = client.post(reverse('wiki.edit_document',
                                               args=[edit_doc.slug],
                                               locale=locale),
                                       edit_data)
                eq_(302, response.status_code)
                # Ensure no redirect
                eq_(0, len(Document.objects.filter(
                                    title=edit_data['title'] + ' Redirect 1',
                                    locale=locale)))
                self.assertRedirects(response,
                                     reverse('wiki.document',
                                             locale=locale,
                                             args=[edit_doc.slug]))

            """ TRANSLATION DOCUMENT TESTING """
            def _run_translate_tests(translate_slug, translate_data,
                                     translate_doc):

                foreign_url = (reverse('wiki.translate',
                                      args=[translate_doc.slug],
                                      locale=locale)
                               + '?tolocale='
                               + foreign_locale)
                foreign_doc_url = reverse('wiki.document',
                                          args=[translate_doc.slug],
                                          locale=foreign_locale)

                # Verify translate page form is populated correctly
                response = client.get(foreign_url)
                eq_(200, response.status_code)
                page = pq(response.content)
                eq_(translate_data['slug'],
                    page.find('input[name=slug]')[0].value)

                # Attempt an invalid edit of the root
                # ensure the slug stays the same (i.e. no parent prepending)
                def test_invalid_slug_translate(inv_slug, url, data):
                    data['slug'] = inv_slug
                    data['form'] = 'both'
                    response = client.post(url, data)
                    eq_(200, response.status_code)  # 200 = bad, invalid data
                    page = pq(response.content)
                    # Slug doesn't add parent
                    eq_(inv_slug, page.find('input[name=slug]')[0].value)
                    self.assertContains(response,
                                        'The slug provided is not valid.')
                    # Ensure no redirect
                    eq_(0, len(Document.objects.filter(title=data['title'] +
                                                   ' Redirect 1',
                                                   locale=foreign_locale)))

                # Push a valid translation
                translate_data['slug'] = translate_slug
                translate_data['form'] = 'both'
                response = client.post(foreign_url, translate_data)
                eq_(302, response.status_code)
                # Ensure no redirect
                eq_(0, len(Document.objects.filter(
                                title=translate_data['title'] + ' Redirect 1',
                                locale=foreign_locale)))
                self.assertRedirects(response, foreign_doc_url)

                return Document.objects.get(locale=foreign_locale,
                                            slug=translate_doc.slug)

            foreign_doc = _run_translate_tests(slug, doc_data, doc)
            foreign_child_doc = _run_translate_tests(child_slug, child_data,
                                                     child_doc)
            foreign_grandchild_doc = _run_translate_tests(grandchild_slug,
                                                          grandchild_data,
                                                          grandchild_doc)

            """ TEST BASIC EDIT OF TRANSLATION """
            def _run_translate_edit_tests(edit_slug, edit_data, edit_doc):

                # Hit the initial URL
                response = client.get(reverse('wiki.edit_document',
                                              args=[edit_doc.slug],
                                              locale=foreign_locale))
                eq_(200, response.status_code)
                page = pq(response.content)
                eq_(edit_data['slug'], page.find('input[name=slug]')[0].value)

                # Attempt an invalid edit of the root, ensure the slug stays
                # the same (i.e. no parent prepending)
                edit_data['slug'] = invalid_slug
                edit_data['form'] = 'both'
                response = client.post(reverse('wiki.edit_document',
                                               args=[edit_doc.slug],
                                               locale=foreign_locale),
                                       edit_data)
                eq_(200, response.status_code)  # 200 = bad, invalid data
                page = pq(response.content)
                # Slug doesn't add parent
                eq_(invalid_slug, page.find('input[name=slug]')[0].value)
                self.assertContains(response, page.find('ul.errorlist li'
                                                        ' a[href="#id_slug"]').
                                    text())
                # Ensure no redirect
                eq_(0, len(Document.objects.filter(title=edit_data['title'] +
                                                   ' Redirect 1',
                                                   locale=foreign_locale)))

                # Push a valid edit, without changing the slug
                edit_data['slug'] = edit_slug
                response = client.post(reverse('wiki.edit_document',
                                               args=[edit_doc.slug],
                                               locale=foreign_locale),
                                       edit_data)
                eq_(302, response.status_code)
                # Ensure no redirect
                eq_(0, len(Document.objects.filter(title=edit_data['title'] +
                                                   ' Redirect 1',
                                                   locale=foreign_locale)))
                self.assertRedirects(response, reverse('wiki.document',
                                                       locale=foreign_locale,
                                                       args=[edit_doc.slug]))

            """ TEST EDITING SLUGS AND TRANSLATIONS """
            def _run_slug_edit_tests(edit_slug, edit_data, edit_doc, loc):

                edit_data['slug'] = edit_data['slug'] + '_Updated'
                edit_data['form'] = 'rev'
                response = client.post(reverse('wiki.edit_document',
                                               args=[edit_doc.slug],
                                               locale=loc),
                                       edit_data)
                eq_(302, response.status_code)
                # HACK: the es doc gets a 'Redirigen 1' if locale/ is updated
                # Ensure *1* redirect
                eq_(1,
                    len(Document.objects.filter(
                        title__contains=edit_data['title'] + ' Redir',
                        locale=loc)))
                self.assertRedirects(response,
                                     reverse('wiki.document',
                                             locale=loc,
                                             args=[edit_doc.slug.replace(
                                                 edit_slug,
                                                 edit_data['slug'])]
                                            )
                                    )

        # Run all of the tests
        _createAndRunTests("parent")

        # Test that slugs with the same "specific" slug but in different levels
        # in the heiharachy are validate properly upon submission

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
        child_url = (reverse('wiki.new_document') +
                     '?parent=' +
                     str(parent_doc.id))
        response = client.post(child_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response,
                             reverse('wiki.document',
                                     args=['length/length'],
                                    locale=settings.WIKI_DEFAULT_LANGUAGE)
                            )

        # Editing "length/length" document doesn't cause errors
        child_data['form'] = 'rev'
        child_data['slug'] = ''
        edit_url = reverse('wiki.edit_document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = client.post(edit_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE))

        # Creating a new translation of "length" and "length/length" doesn't cause errors
        child_data['form'] = 'both'
        child_data['slug'] = 'length'
        translate_url = reverse('wiki.document', args=[child_data['slug']], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=es'
        response = client.post(translate_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=[child_data['slug']], locale='es'))

        translate_url = reverse('wiki.document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=es'
        response = client.post(translate_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=['length/' + child_data['slug']], locale='es'))

    def test_translate_keeps_topical_parent(self):
        client = self.client
        client.login(username='admin', password='testpass')

        en_doc, de_doc = make_translation()

        en_child_doc = document(parent_topic=en_doc, slug='en-child', save=True)
        en_child_rev = revision(document=en_child_doc, save=True)
        de_child_doc = document(parent_topic=de_doc, locale='de', slug='de-child',
                                parent=en_child_doc, save=True)
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

        translate_url = reverse('wiki.edit_document', args=[de_child_doc.slug],
                               locale='de')
        client.post(translate_url, post_data)

        de_child_doc = Document.objects.get(locale='de', slug='de-child')
        eq_(en_child_doc, de_child_doc.parent)
        eq_(de_doc, de_child_doc.parent_topic)
        eq_('New translation', de_child_doc.current_revision.content)


    def test_translate_keeps_toc_depth(self):
        client = self.client
        client.login(username='admin', password='testpass')

        locale = settings.WIKI_DEFAULT_LANGUAGE
        original_slug = 'eng-doc'
        foreign_locale = 'es'
        foreign_slug = 'es-doc'

        en_doc = document(title='Eng Doc', slug=original_slug, is_localizable=True, locale=locale)
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
        translate_url = reverse('wiki.document', args=[original_slug], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=' + foreign_locale
        response = client.post(translate_url, post_data)
        self.assertRedirects(response, reverse('wiki.document', args=[foreign_slug], locale=foreign_locale))

        es_d = Document.objects.get(locale=foreign_locale, slug=foreign_slug)
        eq_(r.toc_depth, es_d.current_revision.toc_depth)

        # Go to edit the translation, ensure the the slug is correct
        response = client.get(reverse('wiki.edit_document', args=[foreign_slug], locale=foreign_locale))
        page = pq(response.content)
        eq_(page.find('input[name=slug]')[0].value, foreign_slug)

    def test_slug_translate(self):
        """Editing a translated doc keeps the correct slug"""
        client = self.client
        client.login(username='admin', password='testpass')

        # Settings
        locale = settings.WIKI_DEFAULT_LANGUAGE
        original_slug = 'eng-doc'
        child_slug = 'child-eng-doc'
        foreign_locale = 'es'
        foreign_slug = 'es-doc'
        foreign_child_slug = 'child-es-doc'

        # Create the one-level English Doc
        en_doc = document(title='Eng Doc', slug=original_slug, is_localizable=True, locale=settings.WIKI_DEFAULT_LANGUAGE)
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
        translate_url = reverse('wiki.document', args=[original_slug], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=' + foreign_locale
        response = client.post(translate_url, parent_data)
        self.assertRedirects(response, reverse('wiki.document', args=[foreign_slug], locale=foreign_locale))

        # Go to edit the translation, ensure the the slug is correct
        response = client.get(reverse('wiki.edit_document', args=[foreign_slug], locale=foreign_locale))
        page = pq(response.content)
        eq_(page.find('input[name=slug]')[0].value, foreign_slug)

        # Create an English child now
        en_doc = document(title='Child Eng Doc', slug=original_slug + '/' + child_slug, is_localizable=True, locale=settings.WIKI_DEFAULT_LANGUAGE, parent_topic=en_doc)
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

        translate_url = reverse('wiki.document', args=[original_slug + '/' + child_slug], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=' + foreign_locale
        response = client.post(translate_url, child_data)
        self.assertRedirects(response, reverse('wiki.document', args=[foreign_slug + '/' + child_data['slug']], locale=foreign_locale))

    def test_clone(self):
        self.client.login(username='admin', password='testpass')

        slug = 'my_doc'
        title = 'My Doc'
        content = '<p>Hello!</p>'

        document = revision(save=True, title=title, slug=slug, content=content).document

        response = self.client.get(reverse('wiki.new_document', args=[], locale=settings.WIKI_DEFAULT_LANGUAGE) + '?clone=' + str(document.id))
        page = pq(response.content)

        eq_(page.find('input[name=title]')[0].value, title)
        eq_(page.find('input[name=slug]')[0].value, slug + '_clone')
        eq_(page.find('textarea[name=content]')[0].value, content)

    def test_localized_based_on(self):
        """Editing a localized article 'based on' an older revision of the
        localization is OK."""
        self.client.login(username='admin', password='testpass')
        en_r = revision(save=True)
        fr_d = document(parent=en_r.document, locale='fr', save=True)
        fr_r = revision(document=fr_d, based_on=en_r, save=True)
        url = reverse('wiki.new_revision_based_on',
                      locale='fr', args=(fr_d.full_path, fr_r.pk,))
        response = self.client.get(url)
        input = pq(response.content)('#id_based_on')[0]
        eq_(int(input.value), en_r.pk)

    def test_restore_translation_source(self):
        """Edit a localized article without an English parent allows user to
        set translation parent."""
        # Create english doc
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        self.client.post(reverse('wiki.new_document'), data)
        en_d = Document.objects.get(locale=data['locale'], slug=data['slug'])

        # Create french doc
        data.update({'locale': 'fr',
                     'full_path': 'fr/a-test-article',
                     'title': 'A Tést Articlé',
                     'content': "C'ést bon."})
        self.client.post(reverse('wiki.new_document', locale='fr'), data)
        fr_d = Document.objects.get(locale=data['locale'], slug=data['slug'])

        # Check edit doc page for choose parent box
        url = reverse('wiki.edit_document', args=[fr_d.slug], locale='fr')
        response = self.client.get(url)
        ok_(pq(response.content)('li.metadata-choose-parent'))

        # Set the parent
        data.update({'form': 'rev', 'parent_id': en_d.id})
        resp = self.client.post(url, data)
        eq_(302, resp.status_code)
        ok_('fr/docs/a-test-article' in resp['Location'])

        # Check the languages drop-down
        resp = self.client.get(resp['Location'])
        translations = pq(resp.content)('ul#translations li')
        ok_('A Test Article' in translations.html())
        ok_('English (US)' in translations.text())

    def test_translation_source(self):
        """Allow users to change "translation source" settings"""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        self.client.post(reverse('wiki.new_document'), data)
        parent = Document.objects.get(locale=data['locale'], slug=data['slug'])

        data.update({'full_path': 'en-US/a-test-article',
                     'title': 'Another Test Article',
                     'content': "Yahoooo!",
                     'parent_id': parent.id})
        self.client.post(reverse('wiki.new_document'), data)
        child = Document.objects.get(locale=data['locale'], slug=data['slug'])

        url = reverse('wiki.edit_document', args=[child.slug])
        response = self.client.get(url)
        content = pq(response.content)
        ok_(content('li.metadata-choose-parent'))
        ok_(str(parent.id) in content.html())

    @attr('tags')
    @mock.patch_object(Site.objects, 'get_current')
    def test_document_tags(self, get_current):
        """Document tags can be edited through revisions"""
        data = new_document_data()
        locale = data['locale']
        slug = data['slug']
        path = slug
        ts1 = ('JavaScript', 'AJAX', 'DOM')
        ts2 = ('XML', 'JSON')

        get_current.return_value.domain = 'su.mo.com'
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        def assert_tag_state(yes_tags, no_tags):

            # Ensure the tags are found for the Documents
            doc = Document.objects.get(locale=locale, slug=slug)
            doc_tags = [x.name for x in doc.tags.all()]
            for t in yes_tags:
                ok_(t in doc_tags)
            for t in no_tags:
                ok_(t not in doc_tags)

            # Ensure the tags are found in the Document view
            response = client.get(reverse('wiki.document',
                                          args=[doc.full_path]), data)
            page = pq(response.content)
            for t in yes_tags:
                eq_(1, page.find('.page-tags li a:contains("%s")' % t).length,
                    '%s should NOT appear in document view tags' % t)
            for t in no_tags:
                eq_(0, page.find('.page-tags li a:contains("%s")' % t).length,
                    '%s should appear in document view tags' % t)

            # Check for the document title in the tag listing
            for t in yes_tags:
                response = client.get(reverse('wiki.tag', args=[t]))
                ok_(doc.title in response.content.decode('utf-8'))
                response = client.get(reverse('wiki.feeds.recent_documents',
                                      args=['atom', t]))
                ok_(doc.title in response.content.decode('utf-8'))

            for t in no_tags:
                response = client.get(reverse('wiki.tag', args=[t]))
                ok_(doc.title not in response.content.decode('utf-8'))
                response = client.get(reverse('wiki.feeds.recent_documents',
                                      args=['atom', t]))
                ok_(doc.title not in response.content.decode('utf-8'))

        # Create a new doc with tags
        data.update({'slug': slug, 'tags': ','.join(ts1)})
        client.post(reverse('wiki.new_document'), data)
        assert_tag_state(ts1, ts2)

        # Now, update the tags.
        data.update({'form': 'rev', 'tags': ', '.join(ts2)})
        client.post(reverse('wiki.edit_document',
                                       args=[path]), data)
        assert_tag_state(ts2, ts1)

    @attr('review_tags')
    @mock.patch_object(Site.objects, 'get_current')
    def test_review_tags(self, get_current):
        """Review tags can be managed on document revisions"""
        get_current.return_value.domain = 'su.mo.com'
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # Create a new doc with one review tag
        data = new_document_data()
        data.update({'review_tags': ['technical']})
        response = client.post(reverse('wiki.new_document'), data)

        # Ensure there's now a doc with that expected tag in its newest
        # revision
        doc = Document.objects.get(slug="a-test-article")
        rev = doc.revisions.order_by('-id').all()[0]
        review_tags = [x.name for x in rev.review_tags.all()]
        eq_(['technical'], review_tags)

        # Now, post an update with two tags
        data.update({
            'form': 'rev',
            'review_tags': ['editorial', 'technical'],
        })
        response = client.post(reverse('wiki.edit_document', args=[doc.full_path]), data)

        # Ensure the doc's newest revision has both tags.
        doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug="a-test-article")
        rev = doc.revisions.order_by('-id').all()[0]
        review_tags = [x.name for x in rev.review_tags.all()]
        review_tags.sort()
        eq_(['editorial', 'technical'], review_tags)

        # Now, ensure that warning boxes appear for the review tags.
        response = client.get(reverse('wiki.document', args=[doc.full_path]), data)
        page = pq(response.content)
        eq_(1, page.find('.warning.review-technical').length)
        eq_(1, page.find('.warning.review-editorial').length)

        # Ensure the page appears on the listing pages
        response = client.get(reverse('wiki.list_review'))
        eq_(1, pq(response.content).find("ul.documents li a:contains('%s')" %
                                         doc.title).length)
        response = client.get(reverse('wiki.list_review_tag',
                                      args=('technical',)))
        eq_(1, pq(response.content).find("ul.documents li a:contains('%s')" %
                                         doc.title).length)
        response = client.get(reverse('wiki.list_review_tag',
                                      args=('editorial',)))
        eq_(1, pq(response.content).find("ul.documents li a:contains('%s')" %
                                         doc.title).length)

        # Also, ensure that the page appears in the proper feeds
        # HACK: Too lazy to parse the XML. Lazy lazy.
        response = client.get(reverse('wiki.feeds.list_review',
                                      args=('atom',)))
        ok_('<entry><title>%s</title>' % doc.title in response.content)
        response = client.get(reverse('wiki.feeds.list_review_tag',
                                      args=('atom', 'technical', )))
        ok_('<entry><title>%s</title>' % doc.title in response.content)
        response = client.get(reverse('wiki.feeds.list_review_tag',
                                      args=('atom', 'editorial', )))
        ok_('<entry><title>%s</title>' % doc.title in response.content)

        # Post an edit that removes one of the tags.
        data.update({
            'form': 'rev',
            'review_tags': ['editorial', ]
        })
        response = client.post(reverse('wiki.edit_document', args=[doc.full_path]), data)

        # Ensure only one of the tags' warning boxes appears, now.
        response = client.get(reverse('wiki.document', args=[doc.full_path]), data)
        page = pq(response.content)
        eq_(0, page.find('.warning.review-technical').length)
        eq_(1, page.find('.warning.review-editorial').length)

        # Ensure the page appears on the listing pages
        response = client.get(reverse('wiki.list_review'))
        eq_(1, pq(response.content).find("ul.documents li a:contains('%s')" %
                                         doc.title).length)
        response = client.get(reverse('wiki.list_review_tag',
                                      args=('technical',)))
        eq_(0, pq(response.content).find("ul.documents li a:contains('%s')" %
                                         doc.title).length)
        response = client.get(reverse('wiki.list_review_tag',
                                      args=('editorial',)))
        eq_(1, pq(response.content).find("ul.documents li a:contains('%s')" %
                                         doc.title).length)

        # Also, ensure that the page appears in the proper feeds
        # HACK: Too lazy to parse the XML. Lazy lazy.
        response = client.get(reverse('wiki.feeds.list_review',
                                      args=('atom',)))
        ok_('<entry><title>%s</title>' % doc.title in response.content)
        response = client.get(reverse('wiki.feeds.list_review_tag',
                                      args=('atom', 'technical', )))
        ok_('<entry><title>%s</title>' % doc.title not in response.content)
        response = client.get(reverse('wiki.feeds.list_review_tag',
                                      args=('atom', 'editorial', )))
        ok_('<entry><title>%s</title>' % doc.title in response.content)

    @attr('review-tags')
    def test_quick_review(self):
        """Test the quick-review button."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        test_data = [
           {'params': {'approve_technical': 1},
            'expected_tags': ['editorial'],
            'name': 'technical',
            'message_contains': ['Technical review completed.']
            },
           {'params': {'approve_editorial': 1},
            'expected_tags': ['technical'],
            'name': 'editorial',
            'message_contains': ['Editorial review completed.']
            },
            {'params': {'approve_technical': 1,
                        'approve_editorial': 1},
             'expected_tags': [],
             'name': 'editorial-technical',
             'message_contains': ['Technical review completed.',
                                  'Editorial review completed.']
             }
            ]

        for data_dict in test_data:
            slug = 'test-quick-review-%s' % data_dict['name']
            data = new_document_data()
            data.update({'review_tags': ['editorial', 'technical'],
                         'slug': slug})
            resp = client.post(reverse('wiki.new_document'), data)

            doc = Document.objects.get(slug=slug)
            rev = doc.revisions.order_by('-id').all()[0]
            review_url = reverse('wiki.quick_review',
                                 args=[doc.full_path])

            params = dict(data_dict['params'], revision_id=rev.id)
            resp = client.post(review_url, params)
            eq_(302, resp.status_code)

            doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug=slug)
            rev = doc.revisions.order_by('-id').all()[0]
            review_tags = [x.name for x in rev.review_tags.all()]
            review_tags.sort()
            for expected_str in data_dict['message_contains']:
                ok_(expected_str in rev.summary)
            eq_(data_dict['expected_tags'], review_tags)

    @attr('midair')
    def test_edit_midair_collision(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # Post a new document.
        data = new_document_data()
        resp = client.post(reverse('wiki.new_document'), data)
        doc = Document.objects.get(slug=data['slug'])

        # Edit #1 starts...
        resp = client.get(reverse('wiki.edit_document', args=[doc.full_path]))
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get(reverse('wiki.edit_document', args=[doc.full_path]))
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': 'This edit got there first',
            'current_rev': rev_id2
        })
        resp = client.post(reverse('wiki.edit_document', args=[doc.full_path]), data)
        eq_(302, resp.status_code)

        # Edit #1 submits, but receives a mid-aired notification
        data.update({
            'form': 'rev',
            'content': 'This edit gets mid-aired',
            'current_rev': rev_id1
        })
        resp = client.post(reverse('wiki.edit_document', args=[doc.full_path]), data)
        eq_(200, resp.status_code)

        ok_(unicode(MIDAIR_COLLISION).encode('utf-8') in resp.content,
            "Midair collision message should appear")

    @attr('toc')
    def test_toc_toggle_off(self):
        """Toggling of table of contents in revisions"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, _ = doc_rev()
        data = new_document_data()
        ok_(Document.objects.get(slug=d.slug, locale=d.locale).show_toc)
        data['form'] = 'rev'
        data['toc_depth'] = 0
        data['slug'] = d.slug
        data['title'] = d.title
        client.post(reverse('wiki.edit_document', args=[d.full_path]), data)
        eq_(0, Document.objects.get(slug=d.slug, locale=d.locale).current_revision.toc_depth)

    @attr('toc')
    def test_toc_toggle_on(self):
        """Toggling of table of contents in revisions"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev()
        new_r = revision(document=d, content=r.content, toc_depth=0,
                         is_approved=True)
        new_r.save()
        ok_(not Document.objects.get(slug=d.slug, locale=d.locale).show_toc)
        data = new_document_data()
        data['form'] = 'rev'
        data['slug'] = d.slug
        data['title'] = d.title
        client.post(reverse('wiki.edit_document', args=[d.full_path]), data)
        ok_(Document.objects.get(slug=d.slug, locale=d.locale).show_toc)

    def test_parent_topic(self):
        """Selection of a parent topic when creating a document."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d = document(title='HTML8')
        d.save()
        r = revision(document=d)
        r.save()

        data = new_document_data()
        data['title'] = 'Replicated local storage'
        data['parent_topic'] = d.id
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)
        ok_(d.children.count() == 1)
        ok_(d.children.all()[0].title == 'Replicated local storage')

    def test_repair_breadcrumbs(self):
        client = LocalizingClient()
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

        client.login(username='admin', password='testpass')

        resp = client.get(reverse('wiki.repair_breadcrumbs',
                                  args=[french_bottom.full_path],
                                  locale='fr'))
        eq_(302, resp.status_code)
        ok_(french_bottom.get_absolute_url() in resp['Location'])

        french_bottom_fixed = Document.objects.get(locale='fr',
                                                   title=french_bottom.title)
        eq_(french_mid.id, french_bottom_fixed.parent_topic.id)
        eq_(french_top.id, french_bottom_fixed.parent_topic.parent_topic.id)


    def test_translate_on_edit(self):
        d1 = document(title="Doc1", locale=settings.WIKI_DEFAULT_LANGUAGE, save=True)
        revision(document=d1, save=True)

        d2 = document(title="TransDoc1", locale='de', parent=d1, save=True)
        revision(document=d2, save=True)

        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        url = reverse('wiki.edit_document', args=(d2.slug,), locale=d2.locale)

        resp = client.get(url)
        eq_(200, resp.status_code)

    def test_discard_location(self):
        """Testing that the 'discard' HREF goes to the correct place when it's
           explicitely and implicitely set"""

        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        def _create_doc(slug, locale):
            doc = document(slug=slug, is_localizable=True, locale=locale)
            doc.save()
            r = revision(document=doc)
            r.save()
            return doc

        # Test that the 'discard' button on an edit goes to the original page
        doc = _create_doc('testdiscarddoc', settings.WIKI_DEFAULT_LANGUAGE)
        response = client.get(reverse('wiki.edit_document', args=[doc.slug], locale=doc.locale))
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.document', args=[doc.slug], locale=doc.locale))

        # Test that the 'discard button on a new translation goes to the en-US page'
        response = client.get(reverse('wiki.translate', args=[doc.slug], locale=doc.locale) + '?tolocale=es')
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.document', args=[doc.slug], locale=doc.locale))

        # Test that the 'discard' button on an existing translation goes to the 'es' page
        foreign_doc = _create_doc('testdiscarddoc', 'es')
        response = client.get(reverse('wiki.edit_document', args=[foreign_doc.slug], locale=foreign_doc.locale))
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.document', args=[foreign_doc.slug], locale=foreign_doc.locale))

        # Test new
        response = client.get(reverse('wiki.new_document', locale=settings.WIKI_DEFAULT_LANGUAGE))
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.new_document', locale=settings.WIKI_DEFAULT_LANGUAGE))

    def test_revert(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        data = new_document_data()
        data['title'] = 'A Test Article For Reverting'
        data['slug'] = 'test-article-for-reverting'
        response = client.post(reverse('wiki.new_document'), data)

        doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                   slug='test-article-for-reverting')
        rev = doc.revisions.order_by('-id').all()[0]

        data['content'] = 'Not lorem ipsum anymore'
        data['comment'] = 'Nobody likes Latin anyway'

        response = client.post(reverse('wiki.edit_document',
                                       args=[doc.full_path]), data)

        response = client.post(reverse('wiki.revert_document',
                                       args=[doc.full_path, rev.id]),
                               {'revert': True, 'comment': 'Blah blah'})

        ok_(302 == response.status_code)
        rev = doc.revisions.order_by('-id').all()[0]
        ok_('lorem ipsum dolor sit amet' == rev.content)
        ok_('Blah blah' in rev.comment)

        rev = doc.revisions.order_by('-id').all()[1]
        response = client.post(reverse('wiki.revert_document',
                                       args=[doc.full_path, rev.id]),
                               {'revert': True})
        ok_(302 == response.status_code)
        rev = doc.revisions.order_by('-id').all()[0]
        ok_(not ': ' in rev.comment)


class DocumentWatchTests(TestCaseBase):
    """Tests for un/subscribing to document edit notifications."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(DocumentWatchTests, self).setUp()
        self.document, self.r = doc_rev()
        self.client.login(username='testuser', password='testpass')

    def test_watch_GET_405(self):
        """Watch document with HTTP GET results in 405."""
        response = get(self.client, 'wiki.document_watch',
                       args=[self.document.slug])
        eq_(405, response.status_code)

    def test_unwatch_GET_405(self):
        """Unwatch document with HTTP GET results in 405."""
        response = get(self.client, 'wiki.document_unwatch',
                       args=[self.document.slug])
        eq_(405, response.status_code)

    def test_watch_unwatch(self):
        """Watch and unwatch a document."""
        user = User.objects.get(username='testuser')
        # Subscribe
        response = post(self.client, 'wiki.document_watch',
                       args=[self.document.slug])
        eq_(200, response.status_code)
        assert EditDocumentEvent.is_notifying(user, self.document), \
               'Watch was not created'
        # Unsubscribe
        response = post(self.client, 'wiki.document_unwatch',
                       args=[self.document.slug])
        eq_(200, response.status_code)
        assert not EditDocumentEvent.is_notifying(user, self.document), \
               'Watch was not destroyed'


class SectionEditingResourceTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_raw_source(self):
        """The raw source for a document can be requested"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
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
        response = client.get('%s?raw=true' %
                              reverse('wiki.document', args=[d.full_path]),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_('Access-Control-Allow-Origin' in response)
        eq_('*', response['Access-Control-Allow-Origin'])
        eq_(normalize_html(expected),
            normalize_html(response.content))

    @attr('bug821986')
    def test_raw_editor_safety_filter(self):
        """Safety filter should be applied before rendering editor"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
            <p onload=alert(3)>FOO</p>
            <svg><circle onload=confirm(3)>HI THERE</circle></svg>
        """)
        response = client.get('%s?raw=true' %
                              reverse('wiki.document', args=[d.full_path]),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_('<p onload=' not in response.content)
        ok_('<circle onload=' not in response.content)

    def test_raw_with_editing_links_source(self):
        """The raw source for a document can be requested, with section editing
        links"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
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
            <h1 id="s1"><a class="edit-section" data-section-id="s1" data-section-src-url="/en-US/docs/%(full_path)s?raw=true&amp;section=s1" href="/en-US/docs/%(full_path)s$edit?section=s1&amp;edit_links=true" title="Edit section">Edit</a>s1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2"><a class="edit-section" data-section-id="s2" data-section-src-url="/en-US/docs/%(full_path)s?raw=true&amp;section=s2" href="/en-US/docs/%(full_path)s$edit?section=s2&amp;edit_links=true" title="Edit section">Edit</a>s2</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s3"><a class="edit-section" data-section-id="s3" data-section-src-url="/en-US/docs/%(full_path)s?raw=true&amp;section=s3" href="/en-US/docs/%(full_path)s$edit?section=s3&amp;edit_links=true" title="Edit section">Edit</a>s3</h1>
            <p>test</p>
            <p>test</p>
        """ % {'full_path': d.full_path}
        response = client.get('%s?raw=true&edit_links=true' %
                              reverse('wiki.document', args=[d.full_path]),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(normalize_html(expected),
            normalize_html(response.content))

    def test_raw_section_source(self):
        """The raw source for a document section can be requested"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
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
        response = client.get('%s?section=s2&raw=true' %
                              reverse('wiki.document', args=[d.full_path]),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(normalize_html(expected),
            normalize_html(response.content))

    @attr('midair')
    @attr('rawsection')
    def test_raw_section_edit(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
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
        expected = """
            <h1 id="s2">s2</h1>
            <p>replace</p>
        """
        response = client.post('%s?section=s2&raw=true' %
                               reverse('wiki.edit_document', args=[d.full_path]),
                               {"form": "rev",
                               'slug': d.slug,
                                "content": replace},
                               follow=True,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(normalize_html(expected),
            normalize_html(response.content))

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
        response = client.get('%s?raw=true' %
                               reverse('wiki.document', args=[d.full_path]),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(normalize_html(expected),
            normalize_html(response.content))

    @attr('midair')
    def test_midair_section_merge(self):
        """If a page was changed while someone was editing, but the changes
        didn't affect the specific section being edited, then ignore the midair
        warning"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        doc, rev = doc_rev("""
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
            <h1 id="s1">replace1</h1>
            <p>replace</p>
        """
        replace_2 = """
            <h1 id="s2">replace2</h1>
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
            'form': 'rev',
            'content': rev.content,
            'slug': ''
        }

        # Edit #1 starts...
        resp = client.get('%s?section=s1' %
                          reverse('wiki.edit_document', args=[doc.full_path]),
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get('%s?section=s2' %
                          reverse('wiki.edit_document', args=[doc.full_path]),
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': replace_2,
            'current_rev': rev_id2,
            'slug': doc.slug
        })
        resp = client.post('%s?section=s2&raw=true' %
                            reverse('wiki.edit_document', args=[doc.full_path]),
                            data,
                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(302, resp.status_code)

        # Edit #1 submits, but since it's a different section, there's no
        # mid-air collision
        data.update({
            'form': 'rev',
            'content': replace_1,
            'current_rev': rev_id1
        })
        resp = client.post('%s?section=s1&raw=true' %
                           reverse('wiki.edit_document', args=[doc.full_path]),
                           data,
                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # No conflict, but we should get a 205 Reset as an indication that the
        # page needs a refresh.
        eq_(205, resp.status_code)

        # Finally, make sure that all the edits landed
        response = client.get('%s?raw=true' %
                               reverse('wiki.document', args=[doc.full_path]),
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(normalize_html(expected),
            normalize_html(response.content))

        # Also, ensure that the revision is slipped into the headers
        eq_(unicode(Document.objects.get(slug=doc.slug, locale=doc.locale)
                                     .current_revision.id),
            unicode(response['x-kuma-revision']))

    @attr('midair')
    def test_midair_section_collision(self):
        """If both a revision and the edited section has changed, then a
        section edit is a collision."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        doc, rev = doc_rev("""
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
            'form': 'rev',
            'content': rev.content
        }

        # Edit #1 starts...
        resp = client.get('%s?section=s2' %
                          reverse('wiki.edit_document', args=[doc.full_path]),
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get('%s?section=s2' %
                          reverse('wiki.edit_document', args=[doc.full_path]),
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': replace_2,
            'slug': doc.slug,
            'current_rev': rev_id2
        })
        resp = client.post('%s?section=s2&raw=true' %
                            reverse('wiki.edit_document', args=[doc.full_path]),
                            data,
                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(302, resp.status_code)

        # Edit #1 submits, but since it's the same section, there's a collision
        data.update({
            'form': 'rev',
            'content': replace_1,
            'current_rev': rev_id1
        })
        resp = client.post('%s?section=s2&raw=true' %
                           reverse('wiki.edit_document', args=[doc.full_path]),
                           data,
                           HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # With the raw API, we should get a 409 Conflict on collision.
        eq_(409, resp.status_code)

    def test_raw_include_option(self):
        doc_src = u"""
            <div class="noinclude">{{ XULRefAttr() }}</div>
            <dl>
              <dt>{{ XULAttr(&quot;maxlength&quot;) }}</dt>
              <dd>Type: <em>integer</em></dd>
              <dd>Przykłady 例 예제 示例</dd>
            </dl>
            <div class="noinclude">
              <p>{{ languages( { &quot;ja&quot;: &quot;ja/XUL/Attribute/maxlength&quot; } ) }}</p>
            </div>
        """
        doc, rev = doc_rev(doc_src)
        expected = u"""
            <dl>
              <dt>{{ XULAttr(&quot;maxlength&quot;) }}</dt>
              <dd>Type: <em>integer</em></dd>
              <dd>Przykłady 例 예제 示例</dd>
            </dl>
        """
        client = LocalizingClient()
        resp = client.get('%s?raw&include' % reverse('wiki.document', args=[doc.full_path]),
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(normalize_html(expected), normalize_html(resp.content.decode('utf-8')))

    def test_section_edit_toc(self):
        """show_toc is preserved in section editing."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        doc, rev = doc_rev("""
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
        response = client.post('%s?section=s2&raw=true' %
                               reverse('wiki.edit_document', args=[doc.full_path]),
                               {"form": "rev",
                               'slug': doc.slug,
                                "content": replace},
                               follow=True,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        changed = Document.objects.get(pk=doc.id).current_revision
        ok_(rev.id != changed.id)
        eq_(1, changed.toc_depth)

    def test_section_edit_review_tags(self):
        """review tags are preserved in section editing."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        doc, rev = doc_rev("""
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
        response = client.post('%s?section=s2&raw=true' %
                               reverse('wiki.edit_document', args=[doc.full_path]),
                               {"form": "rev",
                               'slug': doc.slug,
                                "content": replace},
                               follow=True,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        changed = Document.objects.get(pk=doc.id).current_revision
        ok_(rev.id != changed.id)
        eq_(set(tags_to_save),
            set([t.name for t in changed.review_tags.all()]))


class MindTouchRedirectTests(TestCaseBase):
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

    fixtures = ['test_users.json']

    server_prefix = 'http://testserver/%s/docs' % settings.WIKI_DEFAULT_LANGUAGE
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

    documents = (
        {'title': 'XHTML', 'mt_locale': 'cn', 'kuma_locale': 'zh-CN',
         'expected': '/zh-CN/docs/XHTML'},
        {'title': 'JavaScript', 'mt_locale': 'zh_cn', 'kuma_locale': 'zh-CN',
         'expected': '/zh-CN/docs/JavaScript'},
        {'title': 'XHTML6', 'mt_locale': 'zh_tw', 'kuma_locale': 'zh-CN',
         'expected': '/zh-TW/docs/XHTML6'},
        {'title': 'HTML7', 'mt_locale': 'fr', 'kuma_locale': 'fr',
         'expected': '/fr/docs/HTML7'},
    )

    def test_namespace_urls(self):
        new_doc = document()
        new_doc.title = 'User:Foo'
        new_doc.slug = 'User:Foo'
        new_doc.save()
        for namespace_test in self.namespace_urls:
            resp = self.client.get(namespace_test['mindtouch'], follow=False)
            eq_(301, resp.status_code)
            eq_(namespace_test['kuma'], resp['Location'])

    def test_trailing_slash(self):
        d = document()
        d.locale = 'zh-CN'
        d.slug = 'foofoo'
        d.title = 'FooFoo'
        d.save()
        mt_url = '/cn/%s/' % (d.slug,)
        resp = self.client.get(mt_url)
        eq_(301, resp.status_code)
        eq_('http://testserver%s' % d.get_absolute_url(), resp['Location'])

    def test_document_urls(self):
        for doc in self.documents:
            d = document()
            d.title = doc['title']
            d.slug = doc['title']
            d.locale = doc['kuma_locale']
            d.save()
            mt_url = '/%s' % '/'.join([doc['mt_locale'], doc['title']])
            resp = self.client.get(mt_url)
            eq_(301, resp.status_code)
            eq_('http://testserver%s' % doc['expected'], resp['Location'])

    def test_view_param(self):
        raise SkipTest("WTF does the spot check work but test doesn't?")
        d = document()
        d.locale = settings.WIKI_DEFAULT_LANGUAGE
        d.slug = 'HTML/HTML5'
        d.title = 'HTML 5'
        d.save()
        mt_url = '/en/%s?view=edit' % (d.slug,)
        resp = self.client.get(mt_url)
        eq_(301, resp.status_code)
        expected_url = 'http://testserver%s$edit' % d.get_absolute_url()
        eq_(expected_url, resp['Location'])


class AutosuggestDocumentsTests(TestCaseBase):
    """ Test the we're properly filtering out the Redirects from the document list """

    def test_autosuggest_no_term(self):
        url = reverse('wiki.autosuggest_documents', locale=settings.WIKI_DEFAULT_LANGUAGE)
        resp = self.client.get(url)
        eq_(400, resp.status_code)

    def test_document_redirects(self):

        # All contain "e", so that will be the search term
        invalidDocuments = (
            {'title': 'Something Redirect 8', 'html': 'REDIRECT <a class="redirect" href="/blah">Something Redirect</a>', 'is_redirect': 1},
        )
        validDocuments = (
            {'title': 'e 6', 'html': '<p>Blah text Redirect'},
            {'title': 'e 7', 'html': 'AppleTalk'},
            {'title': 'Response.Redirect'},
        )
        allDocuments = invalidDocuments + validDocuments

        for doc in allDocuments:
            d = document()
            d.title = doc['title']
            if 'html' in doc:
                d.html = doc['html']
            if 'slug' in doc:
                d.slug = doc['slug']
            if 'is_redirect' in doc:
                d.is_redirect = 1
            d.save()

        url = reverse('wiki.autosuggest_documents', locale=settings.WIKI_DEFAULT_LANGUAGE) + '?term=e'
        resp = self.client.get(url)

        ok_('Access-Control-Allow-Origin' in resp)
        eq_('*', resp['Access-Control-Allow-Origin'])

        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_(len(data), len(validDocuments))

        # Ensure that the valid docs found are all in the valid list
        for d in data:
            found = False
            for v in validDocuments:
                if v['title'] in d['title']:
                    found = True
                    break
            eq_(True, found)

    def test_list_no_redirects(self):
        Document.objects.all().delete()

        invalidDocuments = (
            {'title': 'Something Redirect 8', 'slug': 'xx',
                'html': 'REDIRECT <a class="redirect" href="http://davidwalsh.name">yo</a>'},
            {'title': 'My Template', 'slug': 'Template:Something', 'html': 'blah'},
        )
        validDocuments = ({'title': 'A Doc', 'slug': 'blah', 'html': 'Blah blah blah'},)
        allDocuments = invalidDocuments + validDocuments

        for doc in allDocuments:
            d = document(save=True, slug=doc['slug'], title=doc['title'], html=doc['html'])

        resp = self.client.get(reverse('wiki.all_documents', locale=settings.WIKI_DEFAULT_LANGUAGE))
        eq_(len(validDocuments), len(pq(resp.content).find('.documents li')))


class CodeSampleViewTests(TestCaseBase):
    fixtures = ['test_users.json']

    @override_constance_settings(KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/testserver')
    def test_code_sample_1(self):
        """The raw source for a document can be requested"""
        client = LocalizingClient()
        d, r = doc_rev("""
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <p>test</p>
        """)
        expecteds = (
            '<style type="text/css">.some-css { color: red; }</style>',
            'Some HTML',
            '<script type="text/javascript">window.alert("HI THERE")</script>',
        )

        response = client.get(reverse('wiki.code_sample',
                              args=[d.full_path, 'sample1']),
                              HTTP_HOST='testserver')
        ok_('Access-Control-Allow-Origin' in response)
        eq_('*', response['Access-Control-Allow-Origin'])
        eq_(200, response.status_code)
        normalized = normalize_html(response.content)

        # Content checks
        ok_('<!DOCTYPE html>' in response.content)
        for item in expecteds:
            ok_(item in normalized)

    @override_constance_settings(KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/sampleserver')
    def test_code_sample_host_restriction(self):
        client = LocalizingClient()
        d, r = doc_rev("""
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <p>test</p>
        """)

        response = client.get(reverse('wiki.code_sample',
                              args=[d.full_path, 'sample1']),
                              HTTP_HOST='testserver')
        eq_(403, response.status_code)

        response = client.get(reverse('wiki.code_sample',
                              args=[d.full_path, 'sample1']),
                              HTTP_HOST='sampleserver')
        eq_(200, response.status_code)

    @override_constance_settings(KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/sampleserver')
    def test_code_sample_iframe_embed(self):
        slug = 'test-code-embed'
        embed_url = ('https://sampleserver/%s/docs/%s$samples/sample1' %
                     (settings.WIKI_DEFAULT_LANGUAGE, slug))

        doc_src = """
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <iframe id="if1" src="%(embed_url)s"></iframe>
            <iframe id="if2" src="http://testserver"></iframe>
            <iframe id="if3" src="https://some.alien.site.com"></iframe>
            <p>test</p>
        """ % dict(embed_url=embed_url)

        slug = 'test-code-doc'
        client = LocalizingClient()
        d, r = doc_rev()
        revision(save=True, document=d, title="Test code doc", slug=slug,
            content=doc_src)

        response = self.client.get(reverse('wiki.document', args=(d.slug,)))
        eq_(200, response.status_code)

        page = pq(response.content)

        if1 = page.find('#if1')
        eq_(if1.length, 1)
        eq_(if1.attr('src'), embed_url)

        if2 = page.find('#if2')
        eq_(if2.length, 1)
        eq_(if2.attr('src'), '')

        if3 = page.find('#if3')
        eq_(if3.length, 1)
        eq_(if3.attr('src'), '')


class DeferredRenderingViewTests(TestCaseBase):
    """Tests for the deferred rendering system and interaction with views"""

    fixtures = ['test_users.json']

    def setUp(self):
        super(DeferredRenderingViewTests, self).setUp()
        self.rendered_content = 'HELLO RENDERED CONTENT'
        self.raw_content = 'THIS IS RAW CONTENT'

        self.d, self.r = doc_rev(self.raw_content)

        # Disable TOC, makes content inspection easier.
        self.r.toc_depth = 0
        self.r.save()

        self.d.html = self.raw_content
        self.d.rendered_html = self.rendered_content
        self.d.save()

        self.url = reverse('wiki.document',
                           args=(self.d.slug,),
                           locale=self.d.locale)

        constance.config.KUMASCRIPT_TIMEOUT = 5.0
        constance.config.KUMASCRIPT_MAX_AGE = 600

    def tearDown(self):
        super(DeferredRenderingViewTests, self).tearDown()

        constance.config.KUMASCRIPT_TIMEOUT = 0
        constance.config.KUMASCRIPT_MAX_AGE = 0

    @mock.patch('wiki.kumascript.get')
    def test_rendered_content(self, mock_kumascript_get):
        """Document view should serve up rendered content when available"""
        mock_kumascript_get.return_value = (self.rendered_content, None)
        resp = self.client.get(self.url, follow=False)
        p = pq(resp.content)
        txt = p.find('#wikiArticle').text()
        ok_(self.rendered_content in txt)
        ok_(self.raw_content not in txt)

        eq_(0, p.find('#doc-rendering-in-progress').length)
        eq_(0, p.find('#doc-render-raw-fallback').length)

    def test_rendering_in_progress_warning(self):
        """Document view should serve up rendered content when available"""
        # Make the document look like there's a rendering in progress.
        self.d.render_started_at = datetime.datetime.now()
        self.d.save()

        resp = self.client.get(self.url, follow=False)
        p = pq(resp.content)
        txt = p.find('#wikiArticle').text()

        # Even though a rendering looks like it's in progress, ensure the
        # last-known render is displayed.
        ok_(self.rendered_content in txt)
        ok_(self.raw_content not in txt)
        eq_(0, p.find('#doc-rendering-in-progress').length)

        # Only for logged-in users, ensure the render-in-progress warning is
        # displayed.
        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.url, follow=False)
        p = pq(resp.content)
        eq_(1, p.find('#doc-rendering-in-progress').length)

    @mock.patch('wiki.kumascript.get')
    def test_raw_content_during_initial_render(self, mock_kumascript_get):
        """Raw content should be displayed during a document's initial
        deferred rendering"""
        mock_kumascript_get.return_value = (self.rendered_content, None)

        # Make the document look like there's no rendered content, but that a
        # rendering is in progress.
        self.d.html = self.raw_content
        self.d.rendered_html = ''
        self.d.render_started_at = datetime.datetime.now()
        self.d.save()

        # Now, ensure that raw content is shown in the view.
        resp = self.client.get(self.url, follow=False)
        p = pq(resp.content)
        txt = p.find('#wikiArticle').text()
        ok_(self.rendered_content not in txt)
        ok_(self.raw_content in txt)
        eq_(0, p.find('#doc-render-raw-fallback').length)

        # Only for logged-in users, ensure that a warning is displayed about
        # the fallback
        self.client.login(username='testuser', password='testpass')
        resp = self.client.get(self.url, follow=False)
        p = pq(resp.content)
        eq_(1, p.find('#doc-render-raw-fallback').length)

    @attr('schedule_rendering')
    @mock.patch_object(Document, 'schedule_rendering')
    @mock.patch('wiki.kumascript.get')
    def test_schedule_rendering(self, mock_kumascript_get, mock_document_schedule_rendering):
        mock_kumascript_get.return_value = (self.rendered_content, None)

        self.client.login(username='testuser', password='testpass')

        data = new_document_data()
        data.update({
            'form': 'rev',
            'content': 'This is an update',
        })

        edit_url = reverse('wiki.edit_document', args=[self.d.full_path])
        resp = self.client.post(edit_url, data)
        eq_(302, resp.status_code)
        ok_(mock_document_schedule_rendering.called)

        mock_document_schedule_rendering.reset_mock()

        data.update({
            'form': 'both',
            'content': 'This is a translation',
        })
        translate_url = (reverse('wiki.translate', args=[data['slug']],
                                 locale=settings.WIKI_DEFAULT_LANGUAGE) + '?tolocale=fr')
        response = self.client.post(translate_url, data)
        eq_(302, response.status_code)
        ok_(mock_document_schedule_rendering.called)

    @mock.patch('wiki.kumascript.get')
    @mock.patch('requests.post')
    def test_alternate_bleach_whitelist(self, mock_requests_post, mock_kumascript_get):
        # Some test content with contentious tags.
        test_content = """
            <p id="foo">
                <a style="position: absolute; border: 1px;" href="http://example.com">This is a test</a>
                <textarea name="foo"></textarea>
            </p>
        """

        # Expected result filtered through old/current Bleach rules
        expected_content_old = """
            <p id="foo">
                <a style="position: absolute; border: 1px;" href="http://example.com">This is a test</a>
                <textarea name="foo"></textarea>
            </p>
        """

        # Expected result filtered through alternate whitelist
        expected_content_new = """
            <p id="foo">
                <a style="border: 1px;" href="http://example.com">This is a test</a>
                &lt;textarea name="foo"&gt;&lt;/textarea&gt;
            </p>
        """

        # Set up an alternate set of whitelists...
        constance.config.BLEACH_ALLOWED_TAGS = json.dumps([
            "a", "p"
        ])
        constance.config.BLEACH_ALLOWED_ATTRIBUTES = json.dumps({
            "a": ['href', 'style'],
            "p": ['id']
        })
        constance.config.BLEACH_ALLOWED_STYLES = json.dumps([
            "border"
        ])
        constance.config.KUMASCRIPT_TIMEOUT = 100

        # Rig up a mocked response from KumaScript GET method
        mock_kumascript_get.return_value = (test_content, None)

        # Rig up a mocked response from KumaScript POST service
        # Digging a little deeper into the stack, so that the rest of
        # kumascript.post processing happens.
        from StringIO import StringIO
        m_resp = mock.Mock()
        m_resp.status_code = 200
        m_resp.text = test_content
        m_resp.read = StringIO(test_content).read
        mock_requests_post.return_value = m_resp

        d, r = doc_rev(test_content)

        trials = (
            (False, '', expected_content_old),
            (False, '&bleach_new', expected_content_old),
            (True, '', expected_content_old),
            (True, '&bleach_new', expected_content_new),
        )
        for trial in trials:
            do_login, param, expected = trial

            if do_login:
                self.client.login(username='testuser', password='testpass')
            else:
                self.client.logout()

            url = ('%s?raw&macros%s' % (
                   reverse('wiki.document', args=(d.slug,), locale=d.locale),
                   param))
            resp = self.client.get(url, follow=True)
            eq_(normalize_html(expected),
                normalize_html(resp.content),
                "Should match? %s %s %s %s" %
                    (do_login, param, expected, resp.content))


class APITests(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(APITests, self).setUp()

        self.username = 'tester23'
        self.password = 'trustno1'
        self.email = 'tester23@example.com'

        self.user = User(username=self.username,
                         email=self.email)
        self.user.set_password(self.password)
        self.user.save()

        self.key = Key(user=self.user, description='Test Key 1')
        self.secret = self.key.generate_secret()
        self.key_id = self.key.key
        self.key.save()

        auth = '%s:%s' % (self.key_id, self.secret)
        self.basic_auth = 'Basic %s' % base64.encodestring(auth)

        self.client = LocalizingClient()

        self.d, self.r = doc_rev("""
            <h3 id="S1">Section 1</h3>
            <p>This is a page. Deal with it.</p>
            <h3 id="S2">Section 2</h3>
            <p>This is a page. Deal with it.</p>
            <h3 id="S3">Section 3</h3>
            <p>This is a page. Deal with it.</p>
        """)
        self.r.tags = "foo, bar, baz"
        self.r.review_tags.set('technical', 'editorial')
        self.url = self.d.get_absolute_url()

    def tearDown(self):
        super(APITests, self).tearDown()
        Document.objects.filter(current_revision__creator=self.user).delete()
        Revision.objects.filter(creator=self.user).delete()
        Key.objects.filter(user=self.user).delete()
        self.user.delete()

    def test_put_existing(self):
        """PUT API should allow overwrite of existing document content"""
        data = dict(
            summary="Look, I made an edit!",
            content="""
                <p>This is an edit to the page. We've dealt with it.</p>
            """,
        )

        # No auth key leads to a 403 Forbidden
        resp = self._put(self.url, data)
        eq_(403, resp.status_code)

        # But, this should work, given a proper auth key
        resp = self._put(self.url, data,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(205, resp.status_code)

        # Verify the edit happened.
        curr_d = Document.objects.get(pk=self.d.pk)
        eq_(normalize_html(data['content'].strip()),
            normalize_html(Document.objects.get(pk=self.d.pk).html))

        # Also, verify that this resulted in a new revision.
        curr_r = curr_d.current_revision
        ok_(self.r.pk != curr_r.pk)
        eq_(data['summary'], curr_r.summary)
        r_tags = ','.join(sorted(t.name for t in curr_r.review_tags.all()))
        eq_('editorial,technical', r_tags)

    def test_put_section_edit(self):
        """PUT API should allow overwrite of a specific section of an existing
        document"""
        data = dict(
            content="""
                <h3 id="S2">Section 2</h3>
                <p>This is an edit to the page. We've dealt with it.</p>
            """,
            # Along with the section, let's piggyback in some other metadata
            # edits just for good measure. They're not tied to section edit
            # though.
            title="Hahah this is a new title!",
            tags="hello,quux,xyzzy",
            review_tags="technical",
        )

        resp = self._put('%s?section=S2' % self.url, data,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(205, resp.status_code)

        expected = """
            <h3 id="S1">Section 1</h3>
            <p>This is a page. Deal with it.</p>
            <h3 id="S2">Section 2</h3>
            <p>This is an edit to the page. We've dealt with it.</p>
            <h3 id="S3">Section 3</h3>
            <p>This is a page. Deal with it.</p>
        """

        # Verify the section edit happened.
        curr_d = Document.objects.get(pk=self.d.pk)
        eq_(normalize_html(expected.strip()),
            normalize_html(curr_d.html))
        eq_(data['title'], curr_d.title)
        d_tags = ','.join(sorted(t.name for t in curr_d.tags.all()))
        eq_(data['tags'], d_tags)

        # Also, verify that this resulted in a new revision.
        curr_r = curr_d.current_revision
        ok_(self.r.pk != curr_r.pk)
        r_tags = ','.join(sorted(t.name for t in curr_r.review_tags.all()))
        eq_(data['review_tags'], r_tags)

    def test_put_new_root(self):
        """PUT API should allow creation of a document whose path would place
        it at the root of the topic hierarchy."""
        slug = 'new-root-doc'
        url = reverse('wiki.document', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        data = dict(
            title="This is the title of a new page",
            content="""
                <p>This is a new page, hooray!</p>
            """,
            tags="hello,quux,xyzzy",
            review_tags="technical",
        )
        resp = self._put(url, data,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(201, resp.status_code)

    def test_put_new_child(self):
        """PUT API should allow creation of a document whose path would make it
        a child of an existing parent."""
        data = dict(
            title="This is the title of a new page",
            content="""
                <p>This is a new page, hooray!</p>
            """,
            tags="hello,quux,xyzzy",
            review_tags="technical",
        )

        # This first attempt should fail; the proposed parent does not exist.
        url = '%s/nonexistent/newchild' % self.url
        resp = self._put(url, data,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(404, resp.status_code)

        # TODO: I suppose we could rework this part to create the chain of
        # missing parents with stub content, but currently this demands
        # that API users do that themselves.

        # Now, fill in the parent gap...
        p_doc = document(slug='%s/nonexistent' % self.d.slug,
                         locale=settings.WIKI_DEFAULT_LANGUAGE,
                         parent_topic=self.d)
        p_doc.save()
        p_rev = revision(document=p_doc,
                         slug='%s/nonexistent' % self.d.slug,
                         title='I EXIST NOW', save=True)
        p_rev.save()

        # The creation should work, now.
        resp = self._put(url, data,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(201, resp.status_code)

        new_slug = '%s/nonexistent/newchild' % self.d.slug
        new_doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug=new_slug)
        eq_(p_doc.pk, new_doc.parent_topic.pk)

    def test_put_unsupported_content_type(self):
        """PUT API should complain with a 400 Bad Request on an unsupported
        content type submission"""
        slug = 'new-root-doc'
        url = reverse('wiki.document', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        data = "I don't even know what this content is."
        resp = self._put(url, json.dumps(data),
                         content_type='x-super-happy-fun-text',
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(400, resp.status_code)

    def test_put_json(self):
        """PUT API should handle application/json requests"""
        slug = 'new-root-json-doc'
        url = reverse('wiki.document', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        data = dict(
            title="This is the title of a new page",
            content="""
                <p>This is a new page, hooray!</p>
            """,
            tags="hello,quux,xyzzy",
            review_tags="technical",
        )
        resp = self._put(url, json.dumps(data),
                         content_type='application/json',
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(201, resp.status_code)

        new_doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug=slug)
        eq_(data['title'], new_doc.title)
        eq_(normalize_html(data['content']), normalize_html(new_doc.html))

    def test_put_simple_html(self):
        """PUT API should handle text/html requests"""
        slug = 'new-root-html-doc-1'
        url = reverse('wiki.document', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        html = """
            <p>This is a new page, hooray!</p>
        """
        resp = self._put(url, html, content_type='text/html',
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(201, resp.status_code)

        new_doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug=slug)
        eq_(normalize_html(html), normalize_html(new_doc.html))

    def test_put_complex_html(self):
        """PUT API should handle text/html requests with complex HTML documents
        and extract document fields from the markup"""
        slug = 'new-root-html-doc-2'
        url = reverse('wiki.document', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        data = dict(
            title='This is a complex document',
            content="""
                <p>This is a new page, hooray!</p>
            """,
        )
        html = """
            <html>
                <head>
                    <title>%(title)s</title>
                </head>
                <body>%(content)s</body>
            </html>
        """ % data
        resp = self._put(url, html, content_type='text/html',
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(201, resp.status_code)

        new_doc = Document.objects.get(locale=settings.WIKI_DEFAULT_LANGUAGE, slug=slug)
        eq_(data['title'], new_doc.title)
        eq_(normalize_html(data['content']), normalize_html(new_doc.html))

        # TODO: Anything else useful to extract from HTML?
        # Extract tags from head metadata?

    def test_put_track_authkey(self):
        """Revisions modified by PUT API should track the auth key used"""
        slug = 'new-root-doc'
        url = reverse('wiki.document', args=(slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        data = dict(
            title="This is the title of a new page",
            content="""
                <p>This is a new page, hooray!</p>
            """,
            tags="hello,quux,xyzzy",
            review_tags="technical",
        )
        resp = self._put(url, data, HTTP_AUTHORIZATION=self.basic_auth)
        eq_(201, resp.status_code)

        last_log = self.key.history.order_by('-pk').all()[0]
        eq_('created', last_log.action)

        data['title'] = 'New title for old page'
        resp = self._put(url, data, HTTP_AUTHORIZATION=self.basic_auth)
        eq_(205, resp.status_code)

        last_log = self.key.history.order_by('-pk').all()[0]
        eq_('updated', last_log.action)

    def test_put_etag_conflict(self):
        """A PUT request with an if-match header throws a 412 Precondition
        Failed if the underlying document has been changed."""
        resp = self.client.get(self.url)
        orig_etag = resp['ETag']

        content1 = """
            <h2 id="s1">Section 1</h2>
            <p>New section 1</p>
            <h2 id="s2">Section 2</h2>
            <p>New section 2</p>
        """

        # First update should work.
        resp = self._put(self.url, dict(content=content1),
                         HTTP_IF_MATCH=orig_etag,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(205, resp.status_code)

        # Get the new etag, ensure it doesn't match the original.
        resp = self.client.get(self.url)
        new_etag = resp['ETag']
        ok_(orig_etag != new_etag)

        # But, the ETag should have changed, so this update shouldn't work.
        # Using the old ETag suggests a mid-air edit collision happened.
        resp = self._put(self.url, dict(content=content1),
                         HTTP_IF_MATCH=orig_etag,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(412, resp.status_code)

        # Just for good measure, switching to the new ETag should work
        resp = self._put(self.url, dict(content=content1),
                         HTTP_IF_MATCH=new_etag,
                         HTTP_AUTHORIZATION=self.basic_auth)
        eq_(205, resp.status_code)

    def _put(self, path, data={}, content_type=MULTIPART_CONTENT,
             follow=False, **extra):
        """django.test.client.put() does the wrong thing, here. This does
        better, based on post()."""
        if content_type is MULTIPART_CONTENT:
            post_data = encode_multipart(BOUNDARY, data)
        else:
            # Encode the content so that the byte representation is correct.
            match = CONTENT_TYPE_RE.match(content_type)
            if match:
                charset = match.group(1)
            else:
                charset = settings.DEFAULT_CHARSET
            post_data = smart_str(data, encoding=charset)

        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(post_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self.client._get_path(parsed),
            'QUERY_STRING':   parsed[4],
            'REQUEST_METHOD': 'PUT',
            'wsgi.input':     FakePayload(post_data),
        }
        r.update(extra)

        response = self.client.request(**r)
        if follow:
            response = self.client._handle_redirects(response, **extra)
        return response


class AttachmentTests(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_allowed_types = constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES
        constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'

    def tearDown(self):
        constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES = self.old_allowed_types

    def _post_new_attachment(self):
        self.client = Client()  # file views don't need LocalizingClient
        self.client.login(username='admin', password='testpass')

        file_for_upload = make_test_file(
            content='A test file uploaded into kuma.')
        post_data = {
            'title': 'Test uploaded file',
            'description': 'A test file uploaded into kuma.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('wiki.new_attachment'), data=post_data)
        return resp

    def test_legacy_redirect(self):
        self.client = Client()  # file views don't need LocalizingClient
        test_user = User.objects.get(username='testuser2')
        test_file_content = 'Meh meh I am a test file.'
        test_files = (
            {'file_id': 97, 'filename': 'Canvas_rect.png',
             'title': 'Canvas rect', 'slug': 'canvas-rect'},
            {'file_id': 107, 'filename': 'Canvas_smiley.png',
             'title': 'Canvas smiley', 'slug': 'canvas-smiley'},
            {'file_id': 86, 'filename': 'Canvas_lineTo.png',
             'title': 'Canvas lineTo', 'slug': 'canvas-lineto'},
            {'file_id': 55, 'filename': 'Canvas_arc.png',
             'title': 'Canvas arc', 'slug': 'canvas-arc'},
        )
        for f in test_files:
            a = Attachment(title=f['title'], slug=f['slug'],
                           mindtouch_attachment_id=f['file_id'])
            a.save()
            now = datetime.datetime.now()
            r = AttachmentRevision(
                attachment=a,
                mime_type='text/plain',
                title=f['title'],
                slug=f['slug'],
                description='',
                created=now,
                is_approved=True)
            r.creator = test_user
            r.file.save(f['filename'], ContentFile(test_file_content))
            r.make_current()
            mindtouch_url = reverse('wiki.mindtouch_file_redirect',
                                    args=(),
                                    kwargs={'file_id': f['file_id'],
                                            'filename': f['filename']})
            resp = self.client.get(mindtouch_url)
            eq_(301, resp.status_code)
            ok_(a.get_file_url() in resp['Location'])

    def test_new_attachment(self):
        resp = self._post_new_attachment()
        eq_(302, resp.status_code)

        attachment = Attachment.objects.get(title='Test uploaded file')
        eq_(resp['Location'], 'http://testserver%s' % attachment.get_absolute_url())

        rev = attachment.current_revision
        eq_('admin', rev.creator.username)
        eq_('A test file uploaded into kuma.', rev.description)
        eq_('Initial upload', rev.comment)
        ok_(rev.is_approved)

    def test_edit_attachment(self):
        self.client = Client()  # file views don't need LocalizingClient
        self.client.login(username='admin', password='testpass')

        file_for_upload = make_test_file(
            content='I am a test file for editing.')

        post_data = {
            'title': 'Test editing file',
            'description': 'A test file for editing.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('wiki.new_attachment'), data=post_data)

        tdir = tempfile.gettempdir()
        edited_file_for_upload = tempfile.NamedTemporaryFile(suffix=".txt", dir=tdir)
        edited_file_for_upload.write('I am a new version of the test file for editing.')
        edited_file_for_upload.seek(0)

        post_data = {
            'title': 'Test editing file',
            'description': 'A test file for editing.',
            'comment': 'Second revision.',
            'file': edited_file_for_upload,
        }

        attachment = Attachment.objects.get(title='Test editing file')

        resp = self.client.post(reverse('wiki.edit_attachment',
                                        kwargs={'attachment_id': attachment.id}),
                                data=post_data)

        eq_(302, resp.status_code)

        # Re-fetch because it's been updated.
        attachment = Attachment.objects.get(title='Test editing file')
        eq_(resp['Location'], 'http://testserver%s' % attachment.get_absolute_url())

        eq_(2, attachment.revisions.count())

        rev = attachment.current_revision
        eq_('admin', rev.creator.username)
        eq_('Second revision.', rev.comment)
        ok_(rev.is_approved)

        url = attachment.get_file_url()
        resp = self.client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
        eq_('text/plain', rev.mime_type)
        ok_('I am a new version of the test file for editing.' in resp.content)

    def test_attachment_raw_requires_attachment_host(self):
        resp = self._post_new_attachment()
        attachment = Attachment.objects.get(title='Test uploaded file')

        url = attachment.get_file_url()
        resp = self.client.get(url)
        eq_(301, resp.status_code)
        eq_(attachment.get_file_url(), resp['Location'])

        url = attachment.get_file_url()
        resp = self.client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
        eq_('ALLOW-FROM: %s' % settings.DOMAIN, resp['x-frame-options'])
        eq_(200, resp.status_code)

    def test_attachment_detail(self):
        self.client = Client()  # file views don't need LocalizingClient
        self.client.login(username='admin', password='testpass')

        file_for_upload = make_test_file(
            content='I am a test file for attachment detail view.')

        post_data = {
            'title': 'Test file for viewing',
            'description': 'A test file for viewing.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('wiki.new_attachment'), data=post_data)

        attachment = Attachment.objects.get(title='Test file for viewing')

        resp = self.client.get(reverse('wiki.attachment_detail',
                                       kwargs={'attachment_id': attachment.id}))
        eq_(200, resp.status_code)

    def test_get_previous(self):
        """AttachmentRevision.get_previous() should return this revisions's files's
        most recent approved revision."""
        test_user = User.objects.get(username='testuser2')
        a = Attachment(title='Test attachment for get_previous',
                       slug='test-attachment-for-get-previous')
        a.save()
        r = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            slug=a.slug,
            description='',
            comment='Initial revision.',
            created=datetime.datetime.now() - datetime.timedelta(seconds=30),
            creator=test_user,
            is_approved=True)
        r.file.save('get_previous_test_file.txt',
                    ContentFile('I am a test file for get_previous'))
        r.save()
        r.make_current()

        r2 = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            slug=a.slug,
            description='',
            comment='First edit..',
            created=datetime.datetime.now(),
            creator=test_user,
            is_approved=True)
        r2.file.save('get_previous_test_file.txt',
                     ContentFile('I am a test file for get_previous'))
        r2.save()
        r2.make_current()

        eq_(r, r2.get_previous())

    def test_mime_type_filtering(self):
        """Don't allow uploads outside of the explicitly-permitted
        mime-types."""
        #SLIGHT HACK: this requires the default set of allowed
        #mime-types specified in settings.py. Specifically, adding
        #'text/html' to that set will make this test fail.
        test_user = User.objects.get(username='testuser2')
        a = Attachment(title='Test attachment for file type filter',
                       slug='test-attachment-for-file-type-filter')
        a.save()
        r = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            slug=a.slug,
            description='',
            comment='Initial revision.',
            created=datetime.datetime.now() - datetime.timedelta(seconds=30),
            creator=test_user,
            is_approved=True)
        r.file.save('mime_type_filter_test_file.txt',
                    ContentFile('I am a test file for mime-type filtering'))

        self.client = Client()  # file views don't need LocalizingClient
        self.client.login(username='admin', password='testpass')

        # Shamelessly stolen from Django's own file-upload tests.
        tdir = tempfile.gettempdir()
        file_for_upload = tempfile.NamedTemporaryFile(suffix=".html",
                                                      dir=tdir)
        file_for_upload.write('<html>I am a file that tests'
                              'mime-type filtering.</html>.')
        file_for_upload.seek(0)

        post_data = {
            'title': 'Test disallowed file type',
            'description': 'A file kuma should disallow on type.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('wiki.edit_attachment',
                                        kwargs={'attachment_id': a.id}),
                                data=post_data)
        eq_(200, resp.status_code)
        ok_('Files of this type are not permitted.' in resp.content)

    def test_intermediate(self):
        """
        Test that the intermediate DocumentAttachment gets created
        correctly when adding an Attachment with a document_id.

        """
        doc = document(locale='en', slug='attachment-test-intermediate')
        doc.save()
        rev = revision(document=doc, is_approved=True)
        rev.save()

        file_for_upload = make_test_file(
            content='A file for testing intermediate attachment model.')

        post_data = {
            'title': 'Intermediate test file',
            'description': 'Intermediate test file',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        self.client = Client()
        self.client.login(username='admin', password='testpass')

        add_url = urlparams(reverse('wiki.new_attachment'),
                            document_id=doc.id)
        resp = self.client.post(add_url, data=post_data)
        eq_(302, resp.status_code)

        eq_(1, doc.files.count())

        intermediates = DocumentAttachment.objects.filter(document__pk=doc.id)
        eq_(1, intermediates.count())

        intermediate = intermediates[0]
        eq_('admin', intermediate.attached_by.username)
        eq_(file_for_upload.name.split('/')[-1], intermediate.name)

    def test_files_dict(self):
        doc = document(locale='en', slug='attachment-test-files-dict')
        doc.save()
        rev = revision(document=doc, is_approved=True)
        rev.save()

        test_file_1 = make_test_file(
            content='A file for testing the files dict')

        post_data = {
            'title': 'Files dict test file',
            'description': 'Files dict test file',
            'comment': 'Initial upload',
            'file': test_file_1,
        }

        add_url = urlparams(reverse('wiki.new_attachment'),
                            document_id=doc.id)
        self.client = Client()
        self.client.login(username='admin', password='testpass')

        resp = self.client.post(add_url, data=post_data)

        test_file_2 = make_test_file(
            content='Another file for testing the files dict')

        post_data = {
            'title': 'Files dict test file 2',
            'description': 'Files dict test file 2',
            'comment': 'Initial upload',
            'file': test_file_2,
        }

        resp = self.client.post(add_url, data=post_data)

        doc = Document.objects.get(pk=doc.id)

        files_dict = doc.files_dict()

        file1 = files_dict[test_file_1.name.split('/')[-1]]
        eq_('admin', file1['attached_by'])
        eq_('Files dict test file', file1['description'])
        eq_('text/plain', file1['mime_type'])
        ok_(test_file_1.name.split('/')[-1] in file1['url'])

        file2 = files_dict[test_file_2.name.split('/')[-1]]
        eq_('admin', file2['attached_by'])
        eq_('Files dict test file 2', file2['description'])
        eq_('text/plain', file2['mime_type'])
        ok_(test_file_2.name.split('/')[-1] in file2['url'])


class PageMoveTests(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        page_move_flag = Flag.objects.create(name='page_move')
        page_move_flag.users = User.objects.filter(is_superuser=True)
        page_move_flag.save()
        super(PageMoveTests, self).setUp()

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

        conflict = revision(title='Conflict for page-move view',
                            slug='moved/test-page-move-views/test-views',
                            is_approved=True,
                            save=True)

        data = {'slug': 'moved/test-page-move-views'}
        self.client.login(username='admin', password='testpass')
        resp = self.client.post(reverse('wiki.move',
                                        args=(parent_doc.slug,),
                                        locale=parent_doc.locale),
                                data=data)

        eq_(200, resp.status_code)


class DocumentZoneTests(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(DocumentZoneTests, self).setUp()

        root_rev = revision(title='ZoneRoot', slug='ZoneRoot',
                            content='This is the Zone Root',
                            is_approved=True, save=True)
        self.root_doc = root_rev.document

        middle_rev = revision(title='middlePage', slug='middlePage',
                              content='This is a middlepage',
                              is_approved=True, save=True)
        self.middle_doc = middle_rev.document
        self.middle_doc.parent_topic = self.root_doc
        self.middle_doc.save()

        sub_rev = revision(title='SubPage', slug='SubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        self.sub_doc = sub_rev.document
        self.sub_doc.parent_topic = self.middle_doc
        self.sub_doc.save()

        self.root_zone = DocumentZone(document=self.root_doc)
        self.root_zone.styles = """
            article { color: blue; }
        """
        self.root_zone.save()

        self.middle_zone = DocumentZone(document=self.middle_doc)
        self.middle_zone.styles = """
            article { font-weight: bold; }
        """
        self.middle_zone.save()

    def test_zone_styles(self):
        """Ensure CSS styles for a zone can be fetched"""
        url = reverse('wiki.styles', args=(self.root_doc.slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(url, follow=True)
        eq_(self.root_zone.styles, response.content)

        url = reverse('wiki.styles', args=(self.middle_doc.slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(url, follow=True)
        eq_(self.middle_zone.styles, response.content)

        url = reverse('wiki.styles', args=(self.sub_doc.slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(url, follow=True)
        eq_(404, response.status_code)

    def test_zone_styles_links(self):
        """Ensure link to zone style appears in child document views"""
        url = reverse('wiki.document', args=(self.sub_doc.slug,),
                      locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = self.client.get(url, follow=True)

        styles_url = reverse('wiki.styles', args=(self.root_doc.slug,),
                             locale=settings.WIKI_DEFAULT_LANGUAGE)
        root_expected = ('<link rel="stylesheet" type="text/css" href="%s"' %
                         styles_url)
        ok_(root_expected in response.content)

        styles_url = reverse('wiki.styles', args=(self.middle_doc.slug,),
                             locale=settings.WIKI_DEFAULT_LANGUAGE)
        middle_expected = ('<link rel="stylesheet" type="text/css" href="%s"' %
                           styles_url)
        ok_(middle_expected in response.content)
