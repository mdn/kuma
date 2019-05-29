from __future__ import with_statement

import os
import re
from datetime import datetime

from six.moves.urllib.parse import urlparse

from kuma.core.urlresolvers import reverse
from kuma.users.models import User
from kuma.users.tests import UserTestCase
from kuma.wiki.constants import (
    EXPERIMENT_TITLE_PREFIX,
    LEGACY_MINDTOUCH_NAMESPACES
)
from kuma.wiki.templatetags.jinja_helpers import absolutify

from ..models import (
    Document,
    DocumentDeletionLog,
    DocumentSpamAttempt,
    Revision
)
from ..tasks import (build_sitemaps,
                     delete_logs_for_purged_documents,
                     delete_old_documentspamattempt_data)


def test_sitemaps(tmpdir, settings, doc_hierarchy):
    """
    Test the build of the sitemaps.
    """
    settings.SITE_URL = 'https://example.com'
    settings.MEDIA_ROOT = str(tmpdir.mkdir('media'))

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
    for locale, _ in settings.LANGUAGES:
        names = ['sitemap_other.xml']
        actual_locs, actual_lastmods = [], []
        docs = Document.objects.filter(locale=locale)
        if docs.exists():
            names.append('sitemap.xml')
        for name in names:
            sitemap_path = os.path.join('sitemaps', locale, name)
            expected_index_locs.add(absolutify(sitemap_path))
            sitemap_file_path = os.path.join(settings.MEDIA_ROOT, sitemap_path)
            assert os.path.exists(sitemap_file_path)
            with open(sitemap_file_path) as file:
                sitemap = file.read()
                actual_locs.extend(loc_re.findall(sitemap))
                actual_lastmods.extend(lastmod_re.findall(sitemap))

        # Check for duplicates.
        assert len(actual_locs) == len(set(actual_locs))

        expected_locs, expected_lastmods = set(), set()
        expected_locs.add(absolutify(reverse('home', locale=locale)))
        for doc in docs:
            expected_locs.add(absolutify(doc.get_absolute_url()))
            expected_lastmods.add(doc.modified.strftime('%Y-%m-%d'))

        assert set(actual_locs) == expected_locs
        assert set(actual_lastmods) == expected_lastmods

    assert set(actual_index_locs) == expected_index_locs


def test_sitemaps_excluded_documents(tmpdir, settings, wiki_user):
    """
    Test the build of the sitemaps.
    """
    settings.SITE_URL = 'https://example.com'
    settings.MEDIA_ROOT = str(tmpdir.mkdir('media'))
    # Simplify the test
    settings.LANGUAGES = [
        (code, english)
        for code, english in settings.LANGUAGES
        if code in ('en-US', 'sv-SE')
    ]

    top_doc = Document.objects.create(
        locale='en-US',
        slug='top',
        title='Top Document'
    )
    Revision.objects.create(
        document=top_doc,
        creator=wiki_user,
        content='<p>Top...</p>',
        title='Top Document',
        created=datetime(2017, 4, 24, 13, 49)
    )

    # Make one document for every mindtouch legacy namespace.
    for namespace in LEGACY_MINDTOUCH_NAMESPACES:
        legacy_slug = '{}:something'.format(namespace)
        legacy_doc = Document.objects.create(
            locale='en-US',
            slug=legacy_slug,
            title='A Legacy Document'
        )
        Revision.objects.create(
            document=legacy_doc,
            creator=wiki_user,
            content='<p>Legacy...</p>',
            title='Legacy Document',
            created=datetime(2017, 4, 24, 13, 49)
        )

    # Add an "experiment" document
    experiment_slug = EXPERIMENT_TITLE_PREFIX + 'myexperiment'
    experiment_doc = Document.objects.create(
        locale='en-US',
        slug=experiment_slug,
        title='An Experiment Document'
    )
    Revision.objects.create(
        document=experiment_doc,
        creator=wiki_user,
        content='<p>Experiment...</p>',
        title='Experiment Document',
        created=datetime(2017, 4, 24, 13, 49)
    )

    # Add a document with no HTML content
    no_html_slug = 'a-fine-slug'
    no_html_doc = Document.objects.create(
        locale='en-US',
        slug=no_html_slug,
        title='A Lonely Title'
    )
    Revision.objects.create(
        document=no_html_doc,
        creator=wiki_user,
        content='',  # Note!
        title='Just A Title',
        created=datetime(2017, 4, 24, 13, 49)
    )
    assert not no_html_doc.html

    # Add a document without a revision
    no_revision_slug = 'no-revision-slug'
    experiment_doc = Document.objects.create(
        locale='en-US',
        slug=no_revision_slug,
        title='Has no revision yet'
    )

    build_sitemaps()

    all_locs = []
    # Python 3 has support for `glob('**/*.xml')` but for Python 2,
    # we'll have to use os.walk().
    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
        for file in files:
            with open(os.path.join(root, file)) as f:
                content = f.read()
                all_locs.extend(re.findall('<loc>(.*?)</loc>', content))

    # Exclude the inter-linking sitemaps
    all_locs = [loc for loc in all_locs if not loc.endswith('.xml')]

    # Now check exactly which slugs we expect in entirety.
    # Note that this automatically asserts that all the legacy docs
    # created above don't get returned.
    assert set([urlparse(loc).path for loc in all_locs]) == set([
        '/en-US/', '/en-US/docs/top', '/sv-SE/'
    ])


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
