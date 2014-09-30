from __future__ import with_statement
import os
from nose.tools import ok_

from django.conf import settings

from kuma.users.tests import UserTestCase
from kuma.wiki.cron import build_sitemaps
from kuma.wiki.models import Document


class SitemapsTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_sitemaps_files(self):
        """ Comprehensive test of sitemap logic and file writing """
        build_sitemaps()

        expected_sitemap_locs = []
        for locale in Document.objects.distinct().values_list('locale',
                                                              flat=True):
            # we'll expect to see this locale in the sitemap index file
            expected_sitemap_locs.append(
                "<loc>https://example.com/sitemaps/%s/sitemap.xml</loc>" %
                locale
            )
            sitemap_path = os.path.join(settings.MEDIA_ROOT, 'sitemaps',
                                        locale, 'sitemap.xml')
            with open(sitemap_path, 'r') as sitemap_file:
                sitemap_xml = sitemap_file.read()

            docs = (Document.objects.filter(locale=locale)
                                    .exclude(title__startswith='User:')
                                    .exclude(slug__icontains='Talk:'))

            ok_(docs[0].modified.strftime('%Y-%m-%d') in sitemap_xml)
            for doc in docs:
                ok_(doc.slug in sitemap_xml)

        sitemap_path = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
        with open(sitemap_path, 'r') as sitemap_file:
            index_xml = sitemap_file.read()
        for loc in expected_sitemap_locs:
            ok_(loc in index_xml)
