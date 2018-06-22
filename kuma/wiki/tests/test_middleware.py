# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import RequestFactory

from kuma.core.cache import memcache
from kuma.users.tests import UserTestCase

from . import document, revision, WikiTestCase
from ..middleware import DocumentZoneMiddleware
from ..models import DocumentZone


class DocumentZoneMiddlewareTestCase(UserTestCase, WikiTestCase):

    def setUp(self):
        super(DocumentZoneMiddlewareTestCase, self).setUp()
        self.rf = RequestFactory()
        memcache.clear()

        self.zone_root = 'ExtraWiki'
        self.zone_root_content = 'This is the Zone Root'

        root_rev = revision(title='ZoneRoot', slug='Zones/Root',
                            content=self.zone_root_content,
                            is_approved=True, save=True)
        self.root_doc = root_rev.document

        middle_rev = revision(title='middlePage', slug='Zones/Root/Middle',
                              content='This is a middlepage',
                              is_approved=True, save=True)
        self.middle_doc = middle_rev.document
        self.middle_doc.parent_topic = self.root_doc
        self.middle_doc.save()

        sub_rev = revision(title='SubPage', slug='Zones/Root/Middle/SubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        self.sub_doc = sub_rev.document
        self.sub_doc.parent_topic = self.middle_doc
        self.sub_doc.save()

        self.root_zone = DocumentZone(document=self.root_doc)
        self.root_zone.url_root = self.zone_root
        self.root_zone.save()

        self.middle_zone = DocumentZone(document=self.middle_doc)
        self.middle_zone.save()

        other_rev = revision(title='otherPage', slug='otherPage',
                             content='This is an otherpage',
                             is_approved=True, save=True)
        self.other_doc = other_rev.document
        self.other_doc.save()

        self.other_zone = DocumentZone(document=self.other_doc)
        self.other_zone.url_root = ''
        self.other_zone.save()

        # One more doc, just to be sure we can have multiple blank url_roots
        onemore_rev = revision(title='onemorePage', slug='onemorePage',
                               content='This is an onemorepage',
                               is_approved=True, save=True)
        self.onemore_doc = onemore_rev.document
        self.onemore_doc.save()

        self.onemore_zone = DocumentZone(document=self.onemore_doc)
        self.onemore_zone.url_root = ''
        self.onemore_zone.save()

    def test_url_root_internal_redirect(self):
        """Ensure document zone with URL root results in internal redirect"""

        url = '/en-US/%s?raw' % self.zone_root
        response = self.client.get(url, follow=False)
        assert 200 == response.status_code
        assert self.zone_root_content == response.content

        url = '/en-US/%s/Middle/SubPage?raw' % self.zone_root
        response = self.client.get(url, follow=False)
        assert 200 == response.status_code
        assert self.sub_doc.html == response.content

        self.root_zone.url_root = 'NewRoot'
        self.root_zone.save()

        url = '/en-US/%s/Middle/SubPage?raw' % 'NewRoot'
        response = self.client.get(url, follow=False)
        assert 200 == response.status_code
        assert self.sub_doc.html == response.content

    def test_actual_wiki_url_redirect(self):
        """
        Ensure a request for the 'real' path to a document results in a
        redirect to the internal redirect path
        """
        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        assert 302 == response.status_code
        assert response['Location'] == '/en-US/ExtraWiki/Middle?raw=1'

        self.root_zone.url_root = 'NewRoot'
        self.root_zone.save()

        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        assert 302 == response.status_code
        assert response['Location'] == '/en-US/NewRoot/Middle?raw=1'

    def test_blank_url_root(self):
        """Ensure a blank url_root does not trigger URL remap"""
        url = '/en-US/docs/%s?raw=1' % self.other_doc.slug
        response = self.client.get(url, follow=False)
        assert 200 == response.status_code

    def test_no_redirect(self):
        middleware = DocumentZoneMiddleware(lambda req: None)
        for endpoint in ['$subscribe', '$files']:
            request = self.rf.post('/en-US/docs/%s%s?raw' %
                                   (self.other_doc.slug, endpoint))
            assert middleware(request) is None

    def test_skip_no_language_urls(self):
        middleware = DocumentZoneMiddleware(lambda req: None)
        for path in settings.LANGUAGE_URL_IGNORED_PATHS:
            request = self.rf.get('/' + path)
            assert middleware(request) is None

    def test_zone_url_ends_with_slash(self):
        """Ensure urls only rewrite with a '/' at the end of url_root

        bug 1189596
        """
        zone_url_root = 'Firéfox'
        zone_root_content = 'This is the Firéfox zone'

        root_rev = revision(title='Firéfox', slug='Mozilla/Firéfox',
                            content=zone_root_content,
                            is_approved=True, save=True)
        root_doc = root_rev.document

        root_zone = DocumentZone(document=root_doc)
        root_zone.url_root = zone_url_root
        root_zone.save()

        none_zone_rev = revision(title='Firéfox for iOS',
                                 slug='Mozilla/Firéfox_for_iOS',
                                 content='Page outside zone with same prefix',
                                 is_approved=True, save=True)
        non_zone_doc = none_zone_rev.document
        non_zone_doc.save()

        url = '/en-US/docs/%s' % non_zone_doc.slug
        response = self.client.get(url, follow=False)
        assert 200 == response.status_code


class DocumentZoneWithLocaleTestCase(UserTestCase, WikiTestCase):
    """
    Locales and DocumentZones do not always play nicely together, particularly
    with the middleware that attempts to redirect requests to the right
    location. See bug 1267197 for some of the past analysis and discussion.
    """

    def setUp(self):
        super(DocumentZoneWithLocaleTestCase, self).setUp()
        memcache.clear()

        root_rev = revision(title='Firefox', slug='Mozilla/Firefox',
                            is_approved=True, save=True)
        self.en_doc = root_rev.document
        self.en_doc.locale = 'en-US'
        self.en_doc.save()

        self.en_root_zone = DocumentZone(document=self.en_doc, url_root='Firefox')
        self.en_root_zone.save()

        self.fr_doc = document(title='Firefox', slug='Mozilla/Firefox',
                               parent=self.en_doc, locale='fr', save=True)
        revision(document=self.fr_doc, is_approved=True, save=True)

        self.fr_root_zone = DocumentZone(document=self.fr_doc, url_root='Firefox')
        self.fr_root_zone.save()

    def test_zone_with_implied_default_locale(self):
        # This url lacks a locale, so the locale middleware will redirect to the
        # canonical one for the default language.
        url = '/Firefox'
        response = self.client.get(url, follow=False)
        self.assertRedirects(response, '/en-US/Firefox', status_code=302)

    def test_zone_with_default_locale(self):
        # This url is the canonical one for the English zone for this document,
        # so just load it.
        url = '/en-US/Firefox'
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)

    def test_zone_with_non_default_locale(self):
        # This url is the canonical one for the French zone for this document,
        # so just load it.
        url = '/fr/Firefox'
        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)

    def test_docs_zone_with_implied_default_locale(self):
        # This url has no locale and a wiki path, and gets redirected to the
        # zoned url with locale in a single redirect.
        url = '/docs/Firefox'
        response = self.client.get(url, follow=True)
        assert len(response.redirect_chain) == 1
        redirect_url, status_code = response.redirect_chain[0]
        assert redirect_url == '/en-US/Firefox'
        assert status_code == 302

    def test_docs_zone_with_default_locale(self):
        # This url has a locale and a wiki path, and gets redirected to the
        # zoned url.
        url = '/en-US/docs/Firefox'
        response = self.client.get(url, follow=False)
        self.assertRedirects(response, '/en-US/Firefox', status_code=302)

    def test_docs_zone_with_non_default_locale(self):
        # This url has a non-default locale and a wiki path, and gets
        # redirected to the correct zoned url.
        url = '/fr/docs/Firefox'
        response = self.client.get(url, follow=False)
        self.assertRedirects(response, '/fr/Firefox', status_code=302)

    def test_docs_zone_with_get_param_locale(self):
        # This url has no locale and a wiki path, and gets redirected first to
        # the zoned url and then as requested by the ?lang parameter.
        url = '/docs/Firefox'
        response = self.client.get(url, {'lang': 'fr'}, follow=True)
        assert len(response.redirect_chain) == 2
        url1, status_code_1 = response.redirect_chain[0]
        url2, status_code_2 = response.redirect_chain[1]
        assert url1 == '/fr/docs/Firefox'
        assert url2 == '/fr/Firefox'
        assert status_code_1 == status_code_2 == 302

    def test_zone_document_with_implied_default_locale(self):
        # This url has no locale and a wiki path, and gets redirected to the
        # zoned url with locale in a single step.
        url = '/docs/Mozilla/Firefox'
        response = self.client.get(url, follow=True)
        assert len(response.redirect_chain) == 1
        redirect_url, status_code = response.redirect_chain[0]
        assert redirect_url == '/en-US/Firefox'
        assert status_code == 302

    def test_zone_document_with_default_locale(self):
        # This url is the canonical one for our English document, so it should
        # get a single, non-permanent redirect to the zone url.
        url = '/en-US/docs/Mozilla/Firefox'
        response = self.client.get(url, follow=False)
        self.assertRedirects(response, '/en-US/Firefox', status_code=302)

    def test_zone_document_with_non_default_locale(self):
        # This url is the canonical one for our French document, so it should
        # get a single, non-permanent redirect to the zone url.
        url = '/fr/docs/Mozilla/Firefox'
        response = self.client.get(url, follow=False)
        self.assertRedirects(response, '/fr/Firefox', status_code=302)
