import os
import time
from xml.dom.minidom import parseString

from django.db import connection, transaction
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sitemaps import GenericSitemap
from django.template import loader
from django.utils.encoding import smart_str

import cronjobs

from kuma.search.models import DocumentType

from .models import Document


@cronjobs.register
def calculate_related_documents():
    """Calculates all related documents based on common tags."""

    cursor = connection.cursor()

    cursor.execute('DELETE FROM wiki_relateddocument')
    cursor.execute("""
        INSERT INTO
            wiki_relateddocument (document_id, related_id, in_common)
        SELECT
            t1.content_object_id,
            t2.content_object_id,
            COUNT(*) AS common_tags
        FROM
            wiki_document d1 JOIN
            wiki_taggeddocument t1 JOIN
            wiki_taggeddocument t2 JOIN
            wiki_document d2
        WHERE
            d1.id = t1.content_object_id AND
            t1.tag_id = t2.tag_id AND
            t1.content_object_id <> t2.content_object_id AND
            d2.id = t2.content_object_id AND
            d2.locale = d1.locale AND
            d2.category = d1.category AND
            d1.current_revision_id IS NOT NULL AND
            d2.current_revision_id IS NOT NULL
        GROUP BY
            t1.content_object_id,
            t2.content_object_id""")
    transaction.commit_unless_managed()


@cronjobs.register
def build_sitemaps():
    sitemap_element = "<sitemap><loc>%s</loc><lastmod>%s</lastmod></sitemap>"
    sitemap_index = ("<sitemapindex xmlns=\"http://www.sitemaps.org/"
                    "schemas/sitemap/0.9\">")
    for locale in settings.MDN_LANGUAGES:
        queryset = (Document.objects
                        .filter(is_template=False,
                                locale=locale,
                                is_redirect=False)
                        .exclude(title__startswith='User:')
                        .exclude(slug__icontains='Talk:')
                   )
        if len(queryset) > 0:
            info = {'queryset': queryset, 'date_field': 'modified'}
            sitemap = GenericSitemap(info, priority=0.5)
            urls = sitemap.get_urls(page=1)
            xml = smart_str(loader.render_to_string('wiki/sitemap.xml',
                                                    {'urlset': urls}))
            xml = xml.replace('http://developer.mozilla.org',
                              'https://developer.mozilla.org')
            directory = '%s/sitemaps/%s' % (settings.MEDIA_ROOT, locale)
            if not os.path.exists(directory):
                os.makedirs(directory)
            f = open('%s/sitemap.xml' % directory, 'w')
            f.write(xml)
            f.close()

            sitemap_url = ("https://%s/sitemaps/%s/sitemap.xml" % (
                Site.objects.get_current().domain, locale))
            sitemap_index = sitemap_index + sitemap_element % (sitemap_url,
                time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime()))

    sitemap_index = sitemap_index + "</sitemapindex>"
    index_file = open('%s/sitemap.xml' % settings.MEDIA_ROOT, 'w')
    index_file.write(parseString(sitemap_index).toxml())
    index_file.close()


@cronjobs.register
def reindex_documents():
    for id in DocumentType.get_indexable():
        DocumentType.index(DocumentType.extract_document(id), id)
