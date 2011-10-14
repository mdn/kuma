import json

from django.conf import settings
from django.contrib.sites.models import Site

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from wiki.models import VersionMetadata, Document, Revision
from wiki.tests import doc_rev, document, new_document_data, revision
from wiki.views import _version_groups


class VersionGroupTests(TestCase):
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


class RedirectTests(TestCase):
    """Tests for the REDIRECT wiki directive"""

    fixtures = ['test_users.json']

    def test_redirect_suppression(self):
        """The document view shouldn't redirect when passed redirect=no."""
        redirect, _ = doc_rev('REDIRECT [[http://smoo/]]')
        response = self.client.get(
                       redirect.get_absolute_url() + '?redirect=no',
                       follow=True)
        self.assertContains(response, 'REDIRECT ')


class LocaleRedirectTests(TestCase):
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


class ViewTests(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def test_json_view(self):
        url = reverse('wiki.json', force_locale=True)

        resp = self.client.get(url, {'title': 'an article title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('article-title', data['slug'])

        resp = self.client.get(url, {'slug': 'article-title'})
        eq_(200, resp.status_code)
        data = json.loads(resp.content)
        eq_('an article title', data['title'])


class DocumentEditingTests(TestCase):
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
                     'form': 'doc'})
        client.post(reverse('wiki.edit_document', args=[d.slug]), data)
        eq_(new_title, Document.uncached.get(slug=d.slug).title)
        assert "REDIRECT" in Document.uncached.get(title=old_title).html

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
        """Slugs cannot contain /."""

        # FIXME: This test seems broken
        raise SkipTest()

        client = LocalizingClient()
        client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = 'inva/lid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertContains(response, 'The slug provided is not valid.')

        data['slug'] = 'valid'
        response = client.post(reverse('wiki.new_document'), data)
        self.assertRedirects(response, reverse('wiki.document_revisions',
                                               args=[data['slug']],
                                               locale='en-US'))

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
