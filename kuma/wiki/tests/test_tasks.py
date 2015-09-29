from __future__ import with_statement

import os

from django.conf import settings
from django.test import override_settings

import bitly_api
import mock
from nose.tools import eq_, ok_

from kuma.core.cache import memcache
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase, user

from . import document, revision
from ..helpers import absolutify
from ..models import Document
from ..tasks import (build_sitemaps, update_community_stats,
                     update_document_share_url)


class UpdateCommunityStatsTests(UserTestCase):
    contributors = 10

    def setUp(self):
        super(UpdateCommunityStatsTests, self).setUp()
        self.cache = memcache

    def test_empty_community_stats(self):
        update_community_stats()
        stats = self.cache.get('community_stats')
        self.assertIsNone(stats)

    def test_populated_community_stats(self):
        for i in range(self.contributors):
            if i % 2 == 0:
                locale = 'en-US'
            else:
                locale = 'pt-BR'
            test_user = user(save=True)
            doc = document(save=True, locale=locale)
            revision(save=True, creator=test_user, document=doc)

        update_community_stats()
        stats = self.cache.get('community_stats')
        self.assertIsNotNone(stats)
        self.assertIn('contributors', stats)
        self.assertIn('locales', stats)
        self.assertIsInstance(stats['contributors'], long)
        self.assertIsInstance(stats['locales'], long)
        self.assertEqual(stats['contributors'], self.contributors)
        self.assertEqual(stats['locales'], 2)


class SitemapsTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_sitemaps_files(self):
        build_sitemaps()
        locales = (Document.objects.filter_for_list()
                                   .values_list('locale', flat=True))
        expected_sitemap_locs = []
        for locale in set(locales):
            # we'll expect to see this locale in the sitemap index file
            expected_sitemap_locs.append(
                "<loc>https://example.com/sitemaps/%s/sitemap.xml</loc>" %
                locale
            )
            sitemap_path = os.path.join(settings.MEDIA_ROOT, 'sitemaps',
                                        locale, 'sitemap.xml')
            with open(sitemap_path, 'r') as sitemap_file:
                sitemap_xml = sitemap_file.read()

            docs = Document.objects.filter_for_list(locale=locale)

            for doc in docs:
                ok_(doc.modified.strftime('%Y-%m-%d') in sitemap_xml)
                ok_(doc.slug in sitemap_xml)

        sitemap_path = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
        with open(sitemap_path, 'r') as sitemap_file:
            index_xml = sitemap_file.read()
        for loc in expected_sitemap_locs:
            ok_(loc in index_xml)


@override_settings(BITLY_API_KEY='test', BITLY_USERNAME='test')
class BitlyTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def setUp(self):
        super(BitlyTestCase, self).setUp()
        self.long_url = 'http://example.com/long-url'
        self.short_url = 'http://bit.ly/short-url'
        self.doc = Document.objects.get(pk=1)

    @mock.patch('kuma.wiki.tasks.bitly')
    def test_update_document_share_url(self, bitly):
        bitly.shorten.return_value = {'url': self.short_url}
        update_document_share_url(self.doc.pk)
        eq_(bitly.shorten.call_args[0][0],
            absolutify(reverse('wiki.document', args=[self.doc.slug])))
        eq_(Document.objects.get(pk=self.doc.pk).share_url, self.short_url)

    @mock.patch('kuma.wiki.tasks.bitly')
    def test_update_document_share_url_invalid(self, bitly):
        bitly.shorten.return_value = {}
        update_document_share_url(self.doc.pk)
        eq_(self.doc.share_url, None)

    @mock.patch('kuma.wiki.tasks.bitly')
    def test_update_document_share_url_error(self, bitly):
        bitly.shorten.side_effect = bitly_api.BitlyError('500', 'fail')
        update_document_share_url(self.doc.pk)
        eq_(self.doc.share_url, None)
