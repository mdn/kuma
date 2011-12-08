import logging
import json

from django.conf import settings
from django.contrib.sites.models import Site

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

import waffle
from waffle.models import Flag, Sample, Switch

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from . import TestCaseBase

import wiki.content
from wiki.models import VersionMetadata, Document, Revision
from wiki.tests import (doc_rev, document, new_document_data, revision,
                        normalize_html)
from wiki.views import _version_groups
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
        redirect, _ = doc_rev('REDIRECT <a class="redirect" href="http://smoo/">smoo</a>')
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

        # FIXME: This test seems broken
        raise SkipTest()

        en_doc, de_doc = self._create_en_and_de_docs()
        response = self.client.get(reverse('wiki.document',
                                           args=[en_doc.slug],
                                           locale='de'),
                                   follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url())

    def test_fallback_with_query_params(self):
        """The query parameters should be passed along to the redirect."""

        # FIXME: This test seems broken
        raise SkipTest()

        en_doc, de_doc = self._create_en_and_de_docs()
        url = reverse('wiki.document', args=[en_doc.slug], locale='de')
        response = self.client.get(url + '?x=y&x=z', follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url() + '?x=y&x=z')

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
        url = reverse('wiki.json', force_locale=True)

        resp = self.client.get(url, {'title': 'an article title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('article-title', data['slug'])

        url = reverse('wiki.json_slug', args=('article-title',), force_locale=True)
        resp = self.client.get(url)
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('an article title', data['title'])


class DocumentEditingTests(TestCaseBase):
    """Tests for the document-editing view"""

    fixtures = ['test_users.json']

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
        client.post(reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(new_title, Document.uncached.get(slug=d.slug).title)
        assert "REDIRECT" in Document.uncached.get(title=old_title).html

    def test_retitling_ignored_for_iframe(self):
        """When the title of an article is edited in an iframe, the change is
        ignored."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        new_title = 'Some New Title'
        d, r = doc_rev()
        old_title = d.title
        data = new_document_data()
        data.update({'title': new_title,
                     'slug': d.slug,
                     'form': 'rev'})
        client.post('%s?iframe=1' % reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(old_title, Document.uncached.get(slug=d.slug).title)
        assert "REDIRECT" not in Document.uncached.get(title=old_title).html

    @attr('clobber')
    def test_title_slug_collision_errors(self):
        """When an attempt is made to retitle an article and another with that
        title already exists, there should be form errors"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        exist_title = "Existing doc"
        exist_slug = "existing-doc"

        # Create a new doc.
        data = new_document_data()
        data.update({ "title": exist_title, "slug": exist_slug })
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)

        # Create another new doc.
        data = new_document_data()
        data.update({ "title": 'Some new title', "slug": 'some-new-title' })
        response = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)

        # Now, post an update with duplicate slug and title
        data.update({
            'form': 'rev',
            'title': exist_title,
            'slug': exist_slug
        })
        resp = client.post(reverse('wiki.edit_document', args=['some-new-title']), data)
        eq_(200, resp.status_code)
        p = pq(resp.content)

        ok_(p.find('.errorlist').length > 0)
        ok_(p.find('.errorlist a[href="#id_title"]').length > 0)
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

        # Create a new doc.
        data = new_document_data()
        data.update({ "title": exist_title, "slug": exist_slug })
        resp = client.post(reverse('wiki.new_document'), data)
        eq_(302, resp.status_code)

        # Change title and slug
        data.update({'form': 'rev', 
                     'title': "Changed title", 
                     'slug': "changed-title"})
        resp = client.post(reverse('wiki.edit_document', args=[exist_slug]), 
                           data)
        eq_(302, resp.status_code)

        # Change title and slug back to originals, clobbering the redirect
        data.update({'form': 'rev', 
                     'title': exist_title, 
                     'slug': exist_slug})
        resp = client.post(reverse('wiki.edit_document', args=["changed-title"]), 
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
        self.assertRedirects(response, reverse('wiki.document',
                                               args=[data['slug']],
                                               locale='en-US'))

        # Slashes should be fine
        data['title'] = 'valid with slash'
        data['slug'] = 'va/lid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertRedirects(response, reverse('wiki.document',
                                               args=[data['slug']],
                                               locale='en-US'))

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

    def test_localized_based_on(self):
        """Editing a localized article 'based on' an older revision of the
        localization is OK."""

        # FIXME: This test seems broken
        raise SkipTest()

        self.client.login(username='admin', password='testpass')
        en_r = revision(save=True)
        fr_d = document(parent=en_r.document, locale='fr', save=True)
        fr_r = revision(document=fr_d, based_on=en_r, save=True)
        url = reverse('wiki.new_revision_based_on',
                      locale='fr', args=(fr_d.slug, fr_r.pk,))
        response = self.client.get(url)
        input = pq(response.content)('#id_based_on')[0]
        eq_(int(input.value), en_r.pk)

    @attr('review_tags')
    @mock.patch_object(Site.objects, 'get_current')
    def test_review_tags(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        """Review tags can be managed on document revisions"""
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
        response = client.post(reverse('wiki.edit_document', args=[doc.slug]), data)

        # Ensure the doc's newest revision has both tags.
        doc = Document.objects.get(slug="a-test-article")
        rev = doc.revisions.order_by('-id').all()[0]
        review_tags = [x.name for x in rev.review_tags.all()]
        review_tags.sort()
        eq_(['editorial', 'technical'], review_tags)
        
        # Now, ensure that warning boxes appear for the review tags.
        response = client.get(reverse('wiki.document', args=[doc.slug]), data)
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
        response = client.post(reverse('wiki.edit_document', args=[doc.slug]), data)

        # Ensure only one of the tags' warning boxes appears, now.
        response = client.get(reverse('wiki.document', args=[doc.slug]), data)
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
        resp = client.get(reverse('wiki.edit_document', args=[doc.slug]))
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get(reverse('wiki.edit_document', args=[doc.slug]))
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': 'This edit got there first',
            'current_rev': rev_id2
        })
        resp = client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        eq_(302, resp.status_code)

        # Edit #1 submits, but receives a mid-aired notification
        data.update({
            'form': 'rev',
            'content': 'This edit gets mid-aired',
            'current_rev': rev_id1
        })
        resp = client.post(reverse('wiki.edit_document', args=[doc.slug]), data)
        eq_(200, resp.status_code)

        ok_(unicode(MIDAIR_COLLISION).encode('utf-8') in resp.content,
            "Midair collision message should appear")


class SectionEditingResourceTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_raw_source(self):
        """The raw source for a document can be requested"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        response = client.get('%s?raw=true' %
                              reverse('wiki.document', args=[d.slug]))
        eq_(normalize_html(expected), 
            normalize_html(response.content))

    def test_raw_with_editing_links_source(self):
        """The raw source for a document can be requested, with section editing
        links"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        expected = """
            <h1 id="s1"><a class="edit-section" data-section-id="s1" data-section-src-url="/en-US/docs/%(slug)s?raw=true&amp;section=s1" href="/en-US/docs/%(slug)s$edit?section=s1&amp;edit_links=true" title="Edit section">Edit</a>Head 1</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s2"><a class="edit-section" data-section-id="s2" data-section-src-url="/en-US/docs/%(slug)s?raw=true&amp;section=s2" href="/en-US/docs/%(slug)s$edit?section=s2&amp;edit_links=true" title="Edit section">Edit</a>Head 2</h1>
            <p>test</p>
            <p>test</p>
            <h1 id="s3"><a class="edit-section" data-section-id="s3" data-section-src-url="/en-US/docs/%(slug)s?raw=true&amp;section=s3" href="/en-US/docs/%(slug)s$edit?section=s3&amp;edit_links=true" title="Edit section">Edit</a>Head 3</h1>
            <p>test</p>
            <p>test</p>
        """ % {'slug': d.slug}
        response = client.get('%s?raw=true&edit_links=true' %
                              reverse('wiki.document', args=[d.slug]))
        eq_(normalize_html(expected), 
            normalize_html(response.content))

    def test_raw_section_source(self):
        """The raw source for a document section can be requested"""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        expected = """
            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>
        """
        response = client.get('%s?section=s2&raw=true' %
                              reverse('wiki.document', args=[d.slug]))
        eq_(normalize_html(expected), 
            normalize_html(response.content))

    @attr('midair')
    @attr('rawsection')
    def test_raw_section_edit(self):
        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        d, r = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        replace = """
            <h1 id="s2">Replace</h1>
            <p>replace</p>
        """
        expected = """
            <h1 id="s2">Replace</h1>
            <p>replace</p>
        """
        response = client.post('%s?section=s2&raw=true' %
                               reverse('wiki.edit_document', args=[d.slug]),
                               {"form": "rev",
                                "content": replace},
                               follow=True)
        eq_(normalize_html(expected), 
            normalize_html(response.content))

        expected = """
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Replace</h1>
            <p>replace</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        response = client.get('%s?raw=true' %
                               reverse('wiki.document', args=[d.slug]))
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
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """)
        replace_1 = """
            <h1 id="s1">replace</h1>
            <p>replace</p>
        """
        replace_2 = """
            <h1 id="s2">replace</h1>
            <p>replace</p>
        """
        expected = """
            <h1 id="s1">replace</h1>
            <p>replace</p>

            <h1 id="s2">replace</h1>
            <p>replace</p>

            <h1 id="s3">Head 3</h1>
            <p>test</p>
            <p>test</p>
        """
        data = {
            'form': 'rev',
            'content': rev.content
        }

        # Edit #1 starts...
        resp = client.get('%s?section=s1' % 
                          reverse('wiki.edit_document', args=[doc.slug]))
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get('%s?section=s2' % 
                          reverse('wiki.edit_document', args=[doc.slug]))
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': replace_2,
            'current_rev': rev_id2
        })
        resp = client.post('%s?section=s2&raw=true' %
                            reverse('wiki.edit_document', args=[doc.slug]),
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
                           reverse('wiki.edit_document', args=[doc.slug]),
                           data)
        # No conflict, but we should get a 205 Reset as an indication that the
        # page needs a refresh.
        eq_(205, resp.status_code)

        # Finally, make sure that all the edits landed
        response = client.get('%s?raw=true' %
                               reverse('wiki.document', args=[doc.slug]))
        eq_(normalize_html(expected), 
            normalize_html(response.content))

        # Also, ensure that the revision is slipped into the headers
        eq_(unicode(Document.uncached.get(slug=doc.slug).current_revision.id),
            unicode(response['x-kuma-revision']))


    @attr('midair')
    def test_midair_section_collision(self):
        """If both a revision and the edited section has changed, then a
        section edit is a collision."""
        client = LocalizingClient()
        client.login(username='admin', password='testpass')

        doc, rev = doc_rev("""
            <h1 id="s1">Head 1</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s2">Head 2</h1>
            <p>test</p>
            <p>test</p>

            <h1 id="s3">Head 3</h1>
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
                          reverse('wiki.edit_document', args=[doc.slug]))
        page = pq(resp.content)
        rev_id1 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 starts...
        resp = client.get('%s?section=s2' % 
                          reverse('wiki.edit_document', args=[doc.slug]))
        page = pq(resp.content)
        rev_id2 = page.find('input[name="current_rev"]').attr('value')

        # Edit #2 submits successfully
        data.update({
            'form': 'rev',
            'content': replace_2,
            'current_rev': rev_id2
        })
        resp = client.post('%s?section=s2&raw=true' %
                            reverse('wiki.edit_document', args=[doc.slug]),
                            data)
        eq_(302, resp.status_code)

        # Edit #1 submits, but since it's the same section, there's a collision
        data.update({
            'form': 'rev',
            'content': replace_1,
            'current_rev': rev_id1
        })
        resp = client.post('%s?section=s2&raw=true' %
                           reverse('wiki.edit_document', args=[doc.slug]),
                           data)
        # With the raw API, we should get a 409 Conflict on collision.
        eq_(409, resp.status_code)

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
