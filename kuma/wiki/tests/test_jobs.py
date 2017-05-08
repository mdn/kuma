from datetime import datetime

import pytest

from ..models import Revision, DocumentZone
from ..jobs import DocumentZoneStackJob, DocumentContributorsJob


def test_find_roots(db, cleared_cacheback_cache, doc_hierarchy, root_doc):
    """
    Ensure sub pages can find the content zone root.
    """
    def get_zone_stack(doc):
        return DocumentZoneStackJob().get(doc.pk)

    top_doc = doc_hierarchy.top
    middle_top_doc = doc_hierarchy.middle_top
    middle_bottom_doc = doc_hierarchy.middle_bottom
    bottom_doc = doc_hierarchy.bottom

    top_zone = DocumentZone.objects.create(document=top_doc)
    middle_top_zone = DocumentZone.objects.create(document=middle_top_doc)

    assert unicode(top_zone) == u'DocumentZone {} ({})'.format(
        top_doc.get_absolute_url(), top_doc.title)

    assert get_zone_stack(top_doc) == [top_zone]
    assert get_zone_stack(middle_top_doc) == [middle_top_zone, top_zone]
    assert get_zone_stack(middle_bottom_doc) == [middle_top_zone, top_zone]
    assert get_zone_stack(bottom_doc) == [middle_top_zone, top_zone]
    # "root_doc" is an unrelated document.
    assert get_zone_stack(root_doc) == []


@pytest.mark.parametrize("mode", ["maintenance-mode", "normal-mode"])
def test_contributors(db, cleared_cacheback_cache, settings, wiki_user_3,
                      root_doc_with_mixed_contributors, mode):
    """
    Tests basic operation, ordering, caching, and handling of banned and
    inactive contributors.
    """
    settings.MAINTENANCE_MODE = (mode == "maintenance-mode")

    fixture = root_doc_with_mixed_contributors
    root_doc = fixture.doc

    job = DocumentContributorsJob()
    # Set this to true so we bypass the Celery task queue.
    job.fetch_on_miss = True
    contributors = job.get(root_doc.pk)

    if settings.MAINTENANCE_MODE:
        assert not contributors
        return

    valid_contrib_ids = [user.pk for user in fixture.contributors.valid]
    # Banned and inactive contributors should not be included.
    assert [c['id'] for c in contributors] == valid_contrib_ids

    banned_user = fixture.contributors.banned.user

    # Delete the ban.
    fixture.contributors.banned.ban.delete()

    # The freshly un-banned user is now among the contributors because the
    # cache has been invalidated.
    assert banned_user.pk in set(c['id'] for c in job.get(root_doc.pk))

    # Another revision should invalidate the job's cache.
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=wiki_user_3,
        content='<p>The root document re-envisioned.</p>',
        comment='Done with the previous version.',
        created=datetime(2017, 4, 24, 12, 35)
    )
    root_doc.save()

    # The new contributor shows up and is first, followed
    # by the freshly un-banned user, and then the rest.
    assert ([c['id'] for c in job.get(root_doc.pk)] ==
            ([wiki_user_3.pk, banned_user.pk] + valid_contrib_ids))
