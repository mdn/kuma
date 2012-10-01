# coding=utf-8

# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import datetime
import json
import base64
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files import temp as tempfile
from django.db.models import Q
from django.test.client import Client
from django.http import Http404

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

import constance.config

from waffle.models import Flag

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse
from . import TestCaseBase, FakeResponse

from wiki.models import (VersionMetadata, Document, Attachment,
                         AttachmentRevision)
from wiki.tests import (doc_rev, document, new_document_data, revision,
                        normalize_html, create_template_test_users)
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
        url = '/en-US/docs/en-US/'
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

    def test_json_view(self):
        url = reverse('wiki.json', locale='en-US')

        resp = self.client.get(url, {'title': 'an article title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('article-title', data['slug'])

        url = reverse('wiki.json_slug', args=('article-title',),
                      locale='en-US')
        resp = self.client.get(url)
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('an article title', data['title'])


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

        constance.config.KUMASCRIPT_TIMEOUT = 0.0
        constance.config.KUMASCRIPT_MAX_AGE = 600

        # NOTE: We could do this instead of using the @patch decorator over and
        # over, but it requires an upgrade of mock to 0.8.0

        # self.mock_kumascript_get.stop()

    @mock.patch('wiki.kumascript.get')
    def test_basic_view(self, mock_kumascript_get):
        """When kumascript timeout is non-zero, the service should be used"""
        mock_kumascript_get.return_value = (self.d.html, None)
        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        self.client.get(self.url, follow=False)
        ok_(mock_kumascript_get.called,
            "kumascript should have been used")

    @mock.patch('wiki.kumascript.get')
    def test_disabled(self, mock_kumascript_get):
        """When disabled, the kumascript service should not be used"""
        mock_kumascript_get.return_value = (self.d.html, None)
        constance.config.KUMASCRIPT_TIMEOUT = 0.0
        self.client.get(self.url, follow=False)
        ok_(not mock_kumascript_get.called,
            "kumascript not should have been used")

    @mock.patch('wiki.kumascript.get')
    def test_nomacros(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.d.html, None)
        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        self.client.get('%s?nomacros' % self.url, follow=False)
        ok_(not mock_kumascript_get.called,
            "kumascript should not have been used")

    @mock.patch('wiki.kumascript.get')
    def test_raw(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.d.html, None)
        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        self.client.get('%s?raw' % self.url, follow=False)
        ok_(not mock_kumascript_get.called,
            "kumascript should not have been used")

    @mock.patch('wiki.kumascript.get')
    def test_raw_macros(self, mock_kumascript_get):
        mock_kumascript_get.return_value = (self.d.html, None)
        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        self.client.get('%s?raw&macros' % self.url, follow=False)
        ok_(mock_kumascript_get.called,
            "kumascript should have been used")

    @mock.patch('requests.get')
    def test_ua_max_age_zero(self, mock_requests_get):
        """Authenticated users can request a zero max-age for kumascript"""
        trap = {}

        def my_requests_get(url, headers=None, timeout=None):
            trap['headers'] = headers
            return FakeResponse(status_code=200,
                headers={}, body='HELLO WORLD')

        mock_requests_get.side_effect = my_requests_get

        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        constance.config.KUMASCRIPT_MAX_AGE = 1234

        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('max-age=1234', trap['headers']['Cache-Control'])

        self.client.login(username='admin', password='testpass')
        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('no-cache', trap['headers']['Cache-Control'])

    @mock.patch('requests.get')
    def test_ua_no_cache(self, mock_requests_get):
        """Authenticated users can request no-cache for kumascript"""
        trap = {}

        def my_requests_get(url, headers=None, timeout=None):
            trap['headers'] = headers
            return FakeResponse(status_code=200,
                headers={}, body='HELLO WORLD')

        mock_requests_get.side_effect = my_requests_get

        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        constance.config.KUMASCRIPT_MAX_AGE = 1234

        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('max-age=1234', trap['headers']['Cache-Control'])

        self.client.login(username='admin', password='testpass')
        self.client.get(self.url, follow=False,
                HTTP_CACHE_CONTROL='no-cache')
        eq_('no-cache', trap['headers']['Cache-Control'])

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
                return FakeResponse(status_code=200, body=expected_content,
                    headers={
                        "etag": expected_etag,
                        "last-modified": expected_modified,
                        "age": 456
                    })
            else:
                return FakeResponse(status_code=304, body='',
                    headers={
                        "etag": expected_etag,
                        "last-modified": expected_modified,
                        "age": 123
                    })

        mock_requests_get.side_effect = my_requests_get

        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        constance.config.KUMASCRIPT_MAX_AGE = 1234

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
                body='HELLO WORLD',
                headers=headers_out
            )
        mock_requests_get.side_effect = my_requests_get

        # Ensure kumascript is enabled
        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        constance.config.KUMASCRIPT_MAX_AGE = 600

        # Finally, fire off the request to the view and ensure that the log
        # messages were received and displayed on the page. But, only for a
        # logged in user.
        self.client.login(username='admin', password='testpass')
        response = self.client.get(self.url)
        eq_(trap['headers']['X-FireLogger'], '1.2')
        for error in expected_errors['logs']:
            ok_(error['message'] in response.content)

    @mock.patch('requests.post')
    def test_preview_nonascii(self, mock_post):
        """POSTing non-ascii to kumascript should encode to utf8"""
        content = u'Français'
        trap = {}

        def my_post(url, timeout=None, headers=None, data=None):
            trap['data'] = data
            return FakeResponse(status_code=200, headers={},
                                body=content.encode('utf8'))
        mock_post.side_effect = my_post

        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        constance.config.KUMASCRIPT_MAX_AGE = 600

        self.client.login(username='admin', password='testpass')
        self.client.post(reverse('wiki.preview'), {'content': content})
        try:
            trap['data'].decode('utf8')
        except UnicodeDecodeError:
            ok_(False, "Data wasn't posted as utf8")


class DocumentEditingTests(TestCaseBase):
    """Tests for the document-editing view"""

    fixtures = ['test_users.json']

    def test_noindex_post(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        # Go to new document page to ensure no-index header works
        response = client.get(reverse('wiki.new_document', args=[],
                                               locale='en-US'))
        eq_(response['X-Robots-Tag'], 'noindex')


    def test_seo_script(self):

        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        def make_page_and_compare_seo(slug, content, aught_preview):
            # Create the doc
            data = new_document_data()
            data.update({'title': 'blah', 'slug': slug, 'content': content})
            response = client.post(reverse('wiki.new_document',
                                           locale='en-US'),
                                   data)
            eq_(302, response.status_code)

            # Connect to newly created page
            response = self.client.get(reverse('wiki.document', args=[slug],
                                               locale='en-US'))
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
                                  u'<p>I <em>am</em> awesome. <a href="blah">A link</a> is also &lt;cool&gt;</p>',
                                  'I am awesome. A link is also cool')

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

    def test_retitling(self):
        """When the title of an article is edited, a redirect is made."""
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
                     'slug': d.slug,
                     'form': 'rev'})
        client.post(reverse('wiki.edit_document', args=[d.full_path]), data)
        eq_(new_title, Document.uncached.get(slug=d.slug,
                                             locale=d.locale).title)
        assert "REDIRECT" in Document.uncached.get(title=old_title).html

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
        eq_(old_slug, Document.uncached.get(slug=d.slug,
                                             locale=d.locale).slug)
        assert "REDIRECT" not in Document.uncached.get(slug=old_slug).html

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
                                         locale='en-US'))

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


            """ TRANSLATION DOCUMENT TESTING """
            def _run_translate_tests(translate_slug, translate_data, translate_doc):

                foreign_url = reverse('wiki.translate', args=[translate_doc.slug], locale=locale) + '?tolocale=' + foreign_locale
                foreign_doc_url = reverse('wiki.document', args=[translate_doc.slug], locale=foreign_locale)

                # Load the translate page, ensure that the form is populated correctly
                response = client.get(foreign_url)
                eq_(200, response.status_code)
                page = pq(response.content)
                eq_(translate_data['slug'], page.find('input[name=slug]')[0].value)

                # Attempt an invalid edit of the root, ensure the slug stays the same (i.e. no parent prepending)
                def test_invalid_slug_translate(inv_slug, url, data):
                    data['slug'] = inv_slug
                    data['form'] = 'both'
                    response = client.post(url, data)
                    eq_(200, response.status_code) # 200 = bad, invalid data
                    page = pq(response.content)
                    eq_(inv_slug, page.find('input[name=slug]')[0].value) # Slug doesn't add parent
                    self.assertContains(response, 'The slug provided is not valid.')
                    eq_(0, len(Document.objects.filter(title=data['title'] + ' Redirect 1', locale=foreign_locale))) # Ensure no redirect

                test_invalid_slug_translate(invalid_slug1, foreign_url, translate_data)
                test_invalid_slug_translate(invalid_slug2, foreign_url, translate_data)
                test_invalid_slug_translate(invalid_slug3, foreign_url, translate_data)

                # Push a valid translation
                translate_data['slug'] = translate_slug
                translate_data['form'] = 'both'
                response = client.post(foreign_url, translate_data)
                eq_(302, response.status_code)
                eq_(0, len(Document.objects.filter(title=translate_data['title'] + ' Redirect 1', locale=foreign_locale))) # Ensure no redirect
                self.assertRedirects(response, foreign_doc_url)

                return Document.objects.get(locale=foreign_locale, slug=translate_doc.slug)

            foreign_doc = _run_translate_tests(slug, doc_data, doc)
            foreign_child_doc = _run_translate_tests(child_slug, child_data, child_doc)
            foreign_grandchild_doc = _run_translate_tests(grandchild_slug, grandchild_data, grandchild_doc)


            """ TEST BASIC EDIT OF TRANSLATION """
            def _run_translate_edit_tests(edit_slug, edit_data, edit_doc):

                # Hit the initial URL
                response = client.get(reverse('wiki.edit_document', args=[edit_doc.slug], locale=foreign_locale))
                eq_(200, response.status_code)
                page = pq(response.content)
                eq_(edit_data['slug'], page.find('input[name=slug]')[0].value)

                # Attempt an invalid edit of the root, ensure the slug stays the same (i.e. no parent prepending)
                edit_data['slug'] = invalid_slug
                edit_data['form'] = 'both'
                response = client.post(reverse('wiki.edit_document', args=[edit_doc.slug], locale=foreign_locale), edit_data)
                eq_(200, response.status_code) # 200 = bad, invalid data
                page = pq(response.content)
                eq_(invalid_slug, page.find('input[name=slug]')[0].value) # Slug doesn't add parent
                self.assertContains(response, page.find('ul.errorlist li a[href="#id_slug"]').text())
                eq_(0, len(Document.objects.filter(title=edit_data['title'] + ' Redirect 1', locale=foreign_locale))) # Ensure no redirect

                # Push a valid edit, without changing the slug
                edit_data['slug'] = edit_slug
                response = client.post(reverse('wiki.edit_document', args=[edit_doc.slug], locale=foreign_locale), edit_data)
                eq_(302, response.status_code)
                eq_(0, len(Document.objects.filter(title=edit_data['title'] + ' Redirect 1', locale=foreign_locale))) # Ensure no redirect
                self.assertRedirects(response, reverse('wiki.document', locale=foreign_locale, args=[edit_doc.slug]))

            _run_translate_edit_tests(slug, doc_data, foreign_doc)
            _run_translate_edit_tests(child_slug, child_data, foreign_child_doc)
            _run_translate_edit_tests(grandchild_slug, grandchild_data, foreign_grandchild_doc)

        # Run all of the tests
        _createAndRunTests("parent")

        # Test that slugs with the same "specific" slug but in different levels in the heiharachy
        # are validate properly upon submission

        # Create base doc
        parent_doc = document(title='Length', slug='length', is_localizable=True, locale=settings.WIKI_DEFAULT_LANGUAGE)
        parent_doc.save()
        r = revision(document=parent_doc)
        r.save()

        # Create child, try to use same slug, should work
        child_data = new_document_data()
        child_data['title'] = 'Child Length'
        child_data['slug'] = 'length'
        child_data['content'] = 'This is the content'
        child_data['is_localizable'] = True
        child_url = reverse('wiki.new_document') + '?parent=' + str(parent_doc.id)
        response = client.post(child_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE))

        # Editing "length/length" document doesn't cause errors
        child_data['form'] = 'rev'
        edit_url = reverse('wiki.edit_document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE)
        response = client.post(edit_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE))

        # Creating a new translation of "length" and "length/length" doesn't cause errors
        child_data['form'] = 'both'
        translate_url = reverse('wiki.document', args=[child_data['slug']], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=es'
        response = client.post(translate_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=[child_data['slug']], locale='es'))

        translate_url = reverse('wiki.document', args=['length/length'], locale=settings.WIKI_DEFAULT_LANGUAGE) + '$translate?tolocale=es'
        response = client.post(translate_url, child_data)
        eq_(302, response.status_code)
        self.assertRedirects(response, reverse('wiki.document', args=['length/' + child_data['slug']], locale='es'))

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
                eq_(1, page.find('#page-tags li a:contains("%s")' % t).length,
                    '%s should NOT appear in document view tags' % t)
            for t in no_tags:
                eq_(0, page.find('#page-tags li a:contains("%s")' % t).length,
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
        data.update({'review_tags':['technical']})
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
        doc = Document.objects.get(locale='en-US', slug="a-test-article")
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
            'review_tags': ['editorial',],
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
        ok_(Document.uncached.get(slug=d.slug, locale=d.locale).show_toc)
        data['form'] = 'rev'
        del data['show_toc']
        client.post(reverse('wiki.edit_document', args=[d.full_path]), data)
        ok_(not Document.uncached.get(slug=d.slug, locale=d.locale).current_revision.show_toc)

    @attr('toc')
    def test_toc_toggle_on(self):
        """Toggling of table of contents in revisions"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev()
        new_r = revision(document=d, content=r.content, show_toc=False,
                         is_approved=True)
        new_r.save()
        ok_(not Document.uncached.get(slug=d.slug, locale=d.locale).show_toc)
        data = new_document_data()
        data['form'] = 'rev'
        client.post(reverse('wiki.edit_document', args=[d.full_path]), data)
        ok_(Document.uncached.get(slug=d.slug, locale=d.locale).show_toc)

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

    def test_translate_on_edit(self):
        d1 = document(title="Doc1", locale='en-US', save=True)
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
        response = client.get(reverse('wiki.edit_document', args=[doc.slug], locale=doc.locale));
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.document', args=[doc.slug], locale=doc.locale))

        # Test that the 'discard button on a new translation goes to the en-US page'
        response = client.get(reverse('wiki.translate', args=[doc.slug], locale=doc.locale) + '?tolocale=es')
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.document', args=[doc.slug], locale=doc.locale))

        # Test that the 'discard' button on an existing translation goes to the 'es' page
        foreign_doc = _create_doc('testdiscarddoc', 'es')
        response = client.get(reverse('wiki.edit_document', args=[foreign_doc.slug], locale=foreign_doc.locale));
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.document', args=[foreign_doc.slug], locale=foreign_doc.locale))

        # Test new
        response = client.get(reverse('wiki.new_document', locale=settings.WIKI_DEFAULT_LANGUAGE));
        eq_(pq(response.content).find('#btn-discard').attr('href'),
            reverse('wiki.new_document', locale=settings.WIKI_DEFAULT_LANGUAGE))

    def test_revert(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        data = new_document_data()
        data['title'] = 'A Test Article For Reverting'
        data['slug'] = 'test-article-for-reverting'
        response = client.post(reverse('wiki.new_document'), data)

        doc = Document.objects.get(locale='en-US',
                                   slug='test-article-for-reverting')
        rev = doc.revisions.order_by('-id').all()[0]

        data['content'] = 'Not lorem ipsum anymore'
        data['comment'] = 'Nobody likes Latin anyway'

        response = client.post(reverse('wiki.edit_document',
                                       args=[doc.full_path]), data)

        response = client.post(reverse('wiki.revert_document',
                                       args=[doc.full_path, rev.id]),
                               {'revert': True})

        ok_(302 == response.status_code)
        rev = doc.revisions.order_by('-id').all()[0]
        ok_('lorem ipsum dolor sit amet' == rev.content)
        

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
                              reverse('wiki.document', args=[d.full_path]))
        eq_(normalize_html(expected), 
            normalize_html(response.content))

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
                              reverse('wiki.document', args=[d.full_path]))
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
                              reverse('wiki.document', args=[d.full_path]))
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
                               'slug': '',
                                "content": replace},
                               follow=True)
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
                               reverse('wiki.document', args=[d.full_path]))
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
                          reverse('wiki.edit_document', args=[doc.full_path]))
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get('%s?section=s2' % 
                          reverse('wiki.edit_document', args=[doc.full_path]))
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': replace_2,
            'current_rev': rev_id2
        })
        resp = client.post('%s?section=s2&raw=true' %
                            reverse('wiki.edit_document', args=[doc.full_path]),
                            data)
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
                           data)
        # No conflict, but we should get a 205 Reset as an indication that the
        # page needs a refresh.
        eq_(205, resp.status_code)

        # Finally, make sure that all the edits landed
        response = client.get('%s?raw=true' %
                               reverse('wiki.document', args=[doc.full_path]))
        eq_(normalize_html(expected), 
            normalize_html(response.content))

        # Also, ensure that the revision is slipped into the headers
        eq_(unicode(Document.uncached.get(slug=doc.slug, locale=doc.locale)
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
                          reverse('wiki.edit_document', args=[doc.full_path]))
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get('%s?section=s2' %
                          reverse('wiki.edit_document', args=[doc.full_path]))
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': replace_2,
            'slug': '',
            'current_rev': rev_id2
        })
        resp = client.post('%s?section=s2&raw=true' %
                            reverse('wiki.edit_document', args=[doc.full_path]),
                            data)
        eq_(302, resp.status_code)

        # Edit #1 submits, but since it's the same section, there's a collision
        data.update({
            'form': 'rev',
            'content': replace_1,
            'current_rev': rev_id1
        })
        resp = client.post('%s?section=s2&raw=true' %
                           reverse('wiki.edit_document', args=[doc.full_path]),
                           data)
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
        resp = client.get('%s?raw&include' % reverse('wiki.document', args=[doc.full_path]))
        eq_(normalize_html(expected), normalize_html(resp.content.decode('utf-8')))

    @attr('kumawiki')
    def test_kumawiki_waffle_flag(self):

        # Turn off the new wiki for everyone
        self.kumawiki_flag.everyone = False
        self.kumawiki_flag.save()

        client = LocalizingClient()

        resp = client.get(reverse('wiki.all_documents'))
        eq_(404, resp.status_code)

        resp = client.get(reverse('docs'))
        page = pq(resp.content)
        eq_(0, page.find('#kumawiki_preview').length)

        client.login(username='admin', password='testpass')

        # Turn on the wiki for just superusers, ignore everyone else
        self.kumawiki_flag.superusers = True
        self.kumawiki_flag.everyone = None
        self.kumawiki_flag.save()

        resp = client.get(reverse('wiki.all_documents'))
        eq_(200, resp.status_code)

        resp = client.get(reverse('docs'))
        page = pq(resp.content)
        eq_(1, page.find('#kumawiki_preview').length)

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

    namespace_urls = (
        # One for each namespace.
        {'mindtouch': '/Help:Foo',
         'kuma': 'http://testserver/en-US/docs/Help:Foo'},
        {'mindtouch': '/Help_talk:Foo',
         'kuma': 'http://testserver/en-US/docs/Help_talk:Foo'},
        {'mindtouch': '/Project:En/MDC_editor_guide',
         'kuma': 'http://testserver/en-US/docs/Project:MDC_editor_guide'},
        {'mindtouch': '/Project_talk:En/MDC_style_guide',
         'kuma': 'http://testserver/en-US/docs/Project_talk:MDC_style_guide'},
        {'mindtouch': '/Special:Foo',
         'kuma': 'http://testserver/en-US/docs/Special:Foo'},
        {'mindtouch': '/Talk:en/Foo',
         'kuma': 'http://testserver/en-US/docs/Talk:Foo'},
        {'mindtouch': '/Template:Foo',
         'kuma': 'http://testserver/en-US/docs/Template:Foo'},
        {'mindtouch': '/User:Foo',
         'kuma': 'http://testserver/en-US/docs/User:Foo'},
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
        d.locale = 'en-US'
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

    def test_document_redirects(self):

        # All contain "e", so that will be the search term
        invalidDocuments = (
            {'title': 'Redirect 1'},  # Should *not* be returned (first rule)
            {'title': 'e 1', 'html': 'Redirect http//'},  # Should *not* be returned (second rule)
            {'title': 'e 2', 'html': '#Redirect http//'},  # Should *not* be returned (second rule)
            {'title': 'e 3', 'html': '<p>#Redirect http//'},  # Should *not* be returned (second rule)
            {'title': 'e 4', 'html': '<p>Redirect http//'},  # Should *not* be returned (second rule)
            {'title': 'e 5', 'slug': 'Talk:Something'},  # Should *not* be returned (third rule)
        )

        validDocuments = (
            {'title': 'e 6', 'html': '<p>Blah text Redirect'},
            {'title': 'e 7', 'html': 'AppleTalk'},
            {'title': 'Response.Redirect' },
        )

        allDocuments = invalidDocuments + validDocuments

        for doc in allDocuments:
            d = document()
            d.title = doc['title']
            if 'html' in doc:
                d.html = doc['html']
            if 'slug' in doc:
                d.slug = doc['slug']
            d.save()

        url = reverse('wiki.autosuggest_documents', locale='en-US') + '?term=e'
        resp = self.client.get(url)

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

class DeferredRenderingViewTests(TestCaseBase):
    """Tests for the deferred rendering system and interaction with views"""

    fixtures = ['test_users.json']

    def setUp(self):
        super(DeferredRenderingViewTests, self).setUp()
        self.rendered_content = 'HELLO RENDERED CONTENT'
        self.raw_content = 'THIS IS RAW CONTENT'

        self.d, self.r = doc_rev(self.raw_content)

        # Disable TOC, makes content inspection easier.
        self.r.show_toc = False
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

    @mock.patch_object(Document, 'schedule_rendering')
    @mock.patch('wiki.kumascript.get')
    def test_schedule_render_on_edit(self, mock_kumascript_get, mock_document_schedule_rendering):
        mock_kumascript_get.return_value = (self.rendered_content, None)

        self.client.login(username='testuser', password='testpass')
        data = new_document_data()
        data.update({
            'form': 'rev',
            'content': 'This is an update',
        })
        resp = self.client.post(reverse('wiki.edit_document',
                                args=[self.d.full_path]), data)
        eq_(302, resp.status_code)

        ok_(mock_document_schedule_rendering.called)

class AttachmentTests(TestCaseBase):
    fixtures = ['test_users.json']

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
                description = '',
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
        self.client = Client()  # file views don't need LocalizingClient
        self.client.login(username='admin', password='testpass')

        # Shamelessly stolen from Django's own file-upload tests.
        tdir = tempfile.gettempdir()
        file_for_upload = tempfile.NamedTemporaryFile(suffix=".txt", dir=tdir)
        file_for_upload.write('I am a test file for upload.')
        file_for_upload.seek(0)

        post_data = {
            'title': 'Test uploaded file',
            'description': 'A test file uploaded into kuma.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('wiki.new_attachment'), data=post_data)
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

        tdir = tempfile.gettempdir()
        file_for_upload = tempfile.NamedTemporaryFile(suffix=".txt", dir=tdir)
        file_for_upload.write('I am a test file for editing.')
        file_for_upload.seek(0)

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

        resp = self.client.get(attachment.get_file_url())
        eq_('text/plain', rev.mime_type)
        ok_('I am a new version of the test file for editing.' in resp.content)

    def test_attachment_detail(self):
        self.client = Client()  # file views don't need LocalizingClient
        self.client.login(username='admin', password='testpass')

        tdir = tempfile.gettempdir()
        file_for_upload = tempfile.NamedTemporaryFile(suffix=".txt", dir=tdir)
        file_for_upload.write('I am a test file for attachment detail view.')
        file_for_upload.seek(0)

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


class PageMoveTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_move_detection(self):
        """Attempting to change the slug of a page with children will
        redirect to page move interface."""
        parent = revision(title='Test page move views',
                          slug='test-page-move-views',
                          is_approved=True,
                          save=True)

        child = revision(title='Child of page-move view test',
                         slug='page-move/test-views',
                         is_approved=True,
                         save=True)
        child_doc = child.document
        child_doc.parent_topic = parent.document
        child_doc.save()

        data = {'slug': 'change-test-page-move-views'}
        self.client.login(username='admin', password='testpass')
        resp = self.client.post(reverse('wiki.edit_document',
                                        args=(parent.document.slug,),
                                        locale=parent.document.locale),
                                data=data)
        eq_(302, resp.status_code)
        ok_(reverse('wiki.move',
                    args=(parent.document.slug,),
                    locale=parent.document.locale) in resp['Location'])

    def test_move_view(self):
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

        self.client.login(username='admin', password='testpass')
        resp = self.client.get(reverse('wiki.move',
                                       args=(parent_doc.slug,),
                                       locale=parent_doc.locale))
        eq_(200, resp.status_code)

        data = {'slug': 'moved/test-page-move-views'}
        resp = self.client.post(reverse('wiki.move',
                                        args=(parent_doc.slug,),
                                        locale=parent_doc.locale),
                                data=data)
        eq_(302, resp.status_code)
        ok_(reverse('wiki.document',
                    args=('moved/test-page-move-views',),
                    locale=parent_doc.locale) in resp['Location'])
        moved_parent = Document.objects.get(pk=parent_doc.id)
        eq_('moved/test-page-move-views',
            moved_parent.current_revision.slug)
        moved_child = Document.objects.get(pk=child_doc.id)
        eq_('moved/page-move/test-views',
            moved_child.current_revision.slug)

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
                            slug='moved/page-move/test-views',
                            is_approved=True,
                            save=True)

        data = {'slug': 'moved/test-page-move-views'}
        self.client.login(username='admin', password='testpass')
        resp = self.client.post(reverse('wiki.move',
                                        args=(parent_doc.slug,),
                                        locale=parent_doc.locale),
                                data=data)

        eq_(200, resp.status_code)
