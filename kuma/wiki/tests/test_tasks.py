from __future__ import with_statement

import os
import re
from datetime import datetime

import mock
import pytest

from kuma.core.urlresolvers import reverse
from kuma.users.models import User
from kuma.users.tests import UserTestCase
from kuma.wiki.templatetags.jinja_helpers import absolutify

from ..models import Document, DocumentDeletionLog, DocumentSpamAttempt
from ..tasks import (build_sitemaps,
                     delete_logs_for_purged_documents,
                     delete_old_documentspamattempt_data,
                     WikiSitemap)


@pytest.mark.parametrize('max_urls_per_file', (2, 5))
def test_sitemaps(max_urls_per_file, tmpdir, settings, doc_hierarchy):
    """
    Test the build of the sitemaps. There are 4 "en-US" documents in the
    "doc_hierarchy" fixture, as well as one document in each of the "de",
    "fr", and "it" locales. This test covers both the normal case where
    every URL (all of the document URL's as well as the home-page URL) of
    each locale can be placed into a single sitemap file, as well as a
    special case where the "en-US" locale requires mulitple sitemap files
    (max_urls_per_file=2).
    """
    settings.SITE_URL = 'https://example.com'
    settings.MEDIA_ROOT = str(tmpdir.mkdir('media'))
    with mock.patch.object(WikiSitemap, 'limit', max_urls_per_file):
        build_sitemaps()

        loc_re = re.compile(r'<loc>(.+)</loc>')
        lastmod_re = re.compile(r'<lastmod>(.+)</lastmod>')

        sitemap_file_path = os.path.join(settings.MEDIA_ROOT, 'sitemap.xml')
        assert os.path.exists(sitemap_file_path)
        with open(sitemap_file_path) as file:
            actual_index_locs = loc_re.findall(file.read())

        # Check for duplicates.
        assert len(actual_index_locs) == len(set(actual_index_locs))

        expected_index_locs = set()
        sitemap_path_fmt = 'sitemaps/{}/sitemap{}.xml'

        for locale, _ in settings.LANGUAGES:
            postfixes = ['']
            if (locale == 'en-US') and (max_urls_per_file == 2):
                postfixes.extend(('_2', '_3'))

            actual_locs, actual_lastmods = [], []
            for postfix in postfixes:
                sitemap_path = sitemap_path_fmt.format(locale, postfix)
                expected_index_locs.add(absolutify(sitemap_path))
                sitemap_file_path = os.path.join(settings.MEDIA_ROOT,
                                                 sitemap_path)
                assert os.path.exists(sitemap_file_path)
                with open(sitemap_file_path) as file:
                    sitemap = file.read()
                    actual_locs.extend(loc_re.findall(sitemap))
                    actual_lastmods.extend(lastmod_re.findall(sitemap))

            # Check for duplicates.
            assert len(actual_locs) == len(set(actual_locs))

            expected_locs, expected_lastmods = set(), set()
            expected_locs.add(absolutify(reverse('home', locale=locale)))
            for doc in Document.objects.filter(locale=locale).all():
                expected_locs.add(absolutify(doc.get_absolute_url()))
                expected_lastmods.add(doc.modified.strftime('%Y-%m-%d'))

            assert set(actual_locs) == expected_locs
            assert set(actual_lastmods) == expected_lastmods

        assert set(actual_index_locs) == expected_index_locs


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


def test_delete_logs_for_purged_documents(root_doc, wiki_user):
    ddl1 = DocumentDeletionLog.objects.create(
        locale=root_doc.locale, slug=root_doc.slug, user=wiki_user,
        reason='Doomed.')
    root_doc.delete()  # Soft-delete it
    DocumentDeletionLog.objects.create(
        locale='en-US', slug='HardDeleted', user=wiki_user, reason='Purged.')
    delete_logs_for_purged_documents()
    assert list(DocumentDeletionLog.objects.all()) == [ddl1]
