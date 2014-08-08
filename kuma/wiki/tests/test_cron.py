from nose.tools import ok_

from django.conf import settings

from kuma.wiki.cron import build_sitemaps
from kuma.wiki.models import Document
from sumo.tests import TestCase


class SitemapsTestCase(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def test_sitemaps_files(self):
        """ Comprehensive test of sitemap logic and file writing """
        build_sitemaps()

        locale_rows = Document.objects.distinct().values('locale')
        expected_sitemap_locs = []
        for row in locale_rows:
            locale = row['locale']
            # we'll expect to see this locale in the sitemap index file
            expected_sitemap_locs.append(
                "<loc>https://example.com/sitemaps/%s/sitemap.xml</loc>" %
                locale
            )
            sitemap_xml = open('%s/sitemaps/%s/sitemap.xml' %
                               (settings.MEDIA_ROOT, locale), 'r').read()

            docs = (Document.objects.filter(locale=locale)
                                    .exclude(title__startswith='User:')
                                    .exclude(slug__icontains='Talk:'))

            ok_(docs[0].modified.strftime('%Y-%m-%d') in sitemap_xml)
            for doc in docs:
                ok_(doc.slug in sitemap_xml)

        index_xml = open('%s/sitemap.xml' % settings.MEDIA_ROOT, 'r').read()
        for loc in expected_sitemap_locs:
            ok_(loc in index_xml)
