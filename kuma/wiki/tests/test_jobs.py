from datetime import datetime

import pytest

from ..models import Revision, DocumentZone
from ..jobs import DocumentZoneStackJob, DocumentContributorsJob


def test_find_roots(db_and_empty_caches, multi_generational_docs, root_doc):
    """
    Ensure sub pages can find the content zone root.
    """
    def get_zone_stack(doc):
        return DocumentZoneStackJob().get(doc.pk)

    top_doc = multi_generational_docs.great_grandparent
    middle_doc = multi_generational_docs.grandparent
    below_middle_doc = multi_generational_docs.parent
    bottom_doc = multi_generational_docs.child

    top_zone = DocumentZone(document=top_doc)
    top_zone.save()

    middle_zone = DocumentZone(document=middle_doc)
    middle_zone.save()

    assert unicode(top_zone) == u'DocumentZone {} ({})'.format(
        top_doc.get_absolute_url(), top_doc.title)

    assert get_zone_stack(top_doc) == [top_zone]
    assert get_zone_stack(middle_doc) == [middle_zone, top_zone]
    assert get_zone_stack(below_middle_doc) == [middle_zone, top_zone]
    assert get_zone_stack(bottom_doc) == [middle_zone, top_zone]
    # "root_doc" is an unrelated document.
    assert get_zone_stack(root_doc) == []


@pytest.mark.parametrize("mode", ["maintenance-mode", "normal-mode"])
def test_contributors(db_and_empty_caches, settings, wiki_user_3,
                      root_doc_with_mixed_contributors, mode):
    """
    Tests basic operation, ordering, caching, and handling of banned and
    inactive contributors.
    """
    settings.MAINTENANCE_MODE = mode == "maintenance-mode"

    fixture = root_doc_with_mixed_contributors
    root_doc = fixture.doc

    job = DocumentContributorsJob()
    # Set this to true so we bypass the Celery task queue.
    job.fetch_on_miss = True
    contributors = job.get(root_doc.pk)

    if settings.MAINTENANCE_MODE:
        assert not contributors
        return

    # Banned and inactive contributors should not be included.
    expected_contrib_ids = [user.pk for user in fixture.valid_contributors]
    assert [contrib['id'] for contrib in contributors] == expected_contrib_ids

    banned_user = fixture.banned_contributor.user

    # Delete the ban.
    fixture.banned_contributor.ban.delete()

    # The freshly un-banned user is not among the contributors
    # because the cache has not been invalidated.
    assert banned_user.pk not in set(c['id'] for c in job.get(root_doc.pk))

    # Another revision should invalidate the job's cache.
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=wiki_user_3,
        content='<p>The root document re-envisioned.</p>',
        comment='Done with the previous version.',
        created=datetime(2017, 4, 24, 12, 35))
    root_doc.save()

    contributors = job.get(root_doc.pk)
    contrib_ids = [contrib['id'] for contrib in contributors]
    # The new contributor shows up and is first, followed
    # by the freshly un-banned user, and then the rest.
    assert contrib_ids == ([wiki_user_3.pk, banned_user.pk] +
                           expected_contrib_ids)
