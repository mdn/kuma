from __future__ import with_statement

import os
from datetime import datetime

from django.conf import settings

from kuma.users.models import User
from kuma.users.tests import UserTestCase

from ..models import Document, DocumentSpamAttempt
from ..tasks import build_sitemaps, delete_old_documentspamattempt_data


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
                assert doc.modified.strftime('%Y-%m-%d') in sitemap_xml
                assert doc.slug in sitemap_xml

        sitemap_path = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
        with open(sitemap_path, 'r') as sitemap_file:
            index_xml = sitemap_file.read()
        for loc in expected_sitemap_locs:
            assert loc in index_xml


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
