from __future__ import with_statement

from datetime import datetime
import os

from django.conf import settings

from kuma.core.cache import memcache
from kuma.core.tests import ok_
from kuma.users.models import User
from kuma.users.tests import UserTestCase, user

from . import document, revision
from ..models import Document, DocumentSpamAttempt
from ..tasks import (build_sitemaps, delete_old_documentspamattempt_data,
                     update_community_stats)


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


class DeleteOldDocumentSpamAttemptData(UserTestCase):
    fixtures = UserTestCase.fixtures

    def test_delete_old_data(self):
        user = User.objects.get(username='testuser01')
        admin = User.objects.get(username='admin')
        new_dsa = DocumentSpamAttempt.objects.create(
            user=user, title='new record', slug='users:me',
            data='{"PII": "IP, email, etc."}')
        old_reviewed_dsa = DocumentSpamAttempt.objects.create(
            user=user, title='old ham', data='{"PII": "plenty"}',
            review=DocumentSpamAttempt.HAM, reviewer=admin)
        old_unreviewed_dsa = DocumentSpamAttempt.objects.create(
            user=user, title='old unknown', data='{"PII": "yep"}')

        # created is auto-set to current time, update bypasses model logic
        old_date = datetime(2015, 1, 1)
        ids = [old_reviewed_dsa.id, old_unreviewed_dsa.id]
        DocumentSpamAttempt.objects.filter(id__in=ids).update(created=old_date)

        delete_old_documentspamattempt_data()

        new_dsa.refresh_from_db()
        assert new_dsa.data is not None

        old_reviewed_dsa.refresh_from_db()
        assert old_reviewed_dsa.data is None
        assert old_reviewed_dsa.review == DocumentSpamAttempt.HAM

        old_unreviewed_dsa.refresh_from_db()
        assert old_unreviewed_dsa.data is None
        assert old_unreviewed_dsa.review == (
            DocumentSpamAttempt.REVIEW_UNAVAILABLE)
