# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import ok_

from django.conf import settings

from sumo.tests import TestCase
from wiki.cron import build_sitemaps
from wiki.models import Document

from datetime import datetime;

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
                                (settings.MEDIA_ROOT, locale),
                               'r').read()

            docs = Document.objects.filter(locale=locale)

            ok_(docs[0].modified.strftime('%Y-%m-%d') in sitemap_xml)
            for doc in docs:
                ok_(doc.slug in sitemap_xml)

        index_xml = open('%s/sitemap.xml' % settings.MEDIA_ROOT, 'r').read()
        for loc in expected_sitemap_locs:
            ok_(loc in index_xml)
