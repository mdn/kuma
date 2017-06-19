from datetime import datetime

import mock
import pytest

from ..models import Revision
from ..jobs import DocumentNearestZoneJob, DocumentContributorsJob


def test_document_zone_unicode(doc_hierarchy_with_zones):
    top_doc = doc_hierarchy_with_zones.top
    assert unicode(top_doc.zone) == u'DocumentZone {} ({})'.format(
        top_doc.get_absolute_url(), top_doc.title)


def test_nearest_zone_expiry():
    """
    Ensure that the expiry is not constant.
    """
    job = DocumentNearestZoneJob()
    with mock.patch('time.time', return_value=0):
        assert len(set(job.expiry() for _ in range(0, 1000))) > 1


@pytest.mark.parametrize('doc_name,expected_zone_name', [
    ('top', 'top'),
    ('middle_top', 'middle_top'),
    ('middle_bottom', 'middle_top'),
    ('bottom', 'middle_top'),
    ('root', None),
])
def test_nearest_zone(doc_hierarchy_with_zones, root_doc,
                      cleared_cacheback_cache, doc_name, expected_zone_name):
    """
    Test the nearest zone job.
    """
    doc = (root_doc
           if doc_name == 'root' else
           getattr(doc_hierarchy_with_zones, doc_name))
    zone = (None
            if expected_zone_name is None else
            getattr(doc_hierarchy_with_zones, expected_zone_name).zone)
    assert DocumentNearestZoneJob().get(doc.pk) == zone


def test_nearest_zone_when_deleted_parent_topic(doc_hierarchy_with_zones,
                                                cleared_cacheback_cache):
    """
    Make sure we handle the case where we try to get the nearest
    zone for a document whose parent-topic has been deleted.
    """
    bottom_doc = doc_hierarchy_with_zones.bottom
    middle_top_zone = doc_hierarchy_with_zones.middle_top.zone
    # Delete the parent-topic of the bottom doc.
    doc_hierarchy_with_zones.middle_bottom.delete()
    # We should still successfully get the nearest zone for the bottom doc.
    assert DocumentNearestZoneJob().get(bottom_doc.pk) == middle_top_zone


def test_nearest_zone_cache_invalidation_on_save_shallow(doc_hierarchy_with_zones,
                                                         cleared_cacheback_cache):
    job = DocumentNearestZoneJob()

    top_doc = doc_hierarchy_with_zones.top
    middle_top_doc = doc_hierarchy_with_zones.middle_top
    middle_bottom_doc = doc_hierarchy_with_zones.middle_bottom
    bottom_doc = doc_hierarchy_with_zones.bottom

    top_zone = top_doc.zone
    middle_top_zone = middle_top_doc.zone

    # Load the cache for each of the docs.
    assert job.get(top_doc.pk) == top_zone
    assert job.get(middle_top_doc.pk) == middle_top_zone
    assert job.get(middle_bottom_doc.pk) == middle_top_zone
    assert job.get(bottom_doc.pk) == middle_top_zone

    # Change and save a field (other than the document id) on the top zone.
    assert top_zone.css_slug == 'lindsey'
    with mock.patch('kuma.wiki.jobs.DocumentNearestZoneJob.refresh',
                    wraps=job.refresh) as mock_refresh:
        top_zone.css_slug = 'christine'
        top_zone.save()

    # Only the cache for the top doc should have been invalidated.
    assert job.get(top_doc.pk).css_slug == 'christine'
    mock_refresh.assert_called_once_with(top_doc.pk)


def test_nearest_zone_cache_invalidation_on_save_deep(doc_hierarchy_with_zones,
                                                      cleared_cacheback_cache):
    job = DocumentNearestZoneJob()

    top_doc = doc_hierarchy_with_zones.top
    middle_top_doc = doc_hierarchy_with_zones.middle_top
    middle_bottom_doc = doc_hierarchy_with_zones.middle_bottom
    bottom_doc = doc_hierarchy_with_zones.bottom

    top_zone = top_doc.zone
    middle_top_zone = middle_top_doc.zone

    # Load the cache for each of the docs.
    assert job.get(top_doc.pk) == top_zone
    assert job.get(middle_top_doc.pk) == middle_top_zone
    assert job.get(middle_bottom_doc.pk) == middle_top_zone
    assert job.get(bottom_doc.pk) == middle_top_zone

    # Change and save a field (other than the document id) on a zone,
    # but this time the invalidation process should descend to the bottom.
    assert middle_top_zone.css_slug == 'bobby'
    with mock.patch('kuma.wiki.jobs.DocumentNearestZoneJob.refresh',
                    wraps=job.refresh) as mock_refresh:
        middle_top_zone.css_slug = 'henry'
        middle_top_zone.save()

    # The cache for the middle-top doc and its descendants should have been
    # invalidated.
    assert job.get(middle_top_doc.pk).css_slug == 'henry'
    assert job.get(middle_bottom_doc.pk).css_slug == 'henry'
    assert job.get(bottom_doc.pk).css_slug == 'henry'

    assert mock_refresh.call_count == 3
    mock_refresh.assert_has_calls([
        mock.call(middle_top_doc.pk),
        mock.call(middle_bottom_doc.pk),
        mock.call(bottom_doc.pk)
    ], any_order=True)


def test_nearest_zone_cache_invalidation_on_save_doc_id(doc_hierarchy_with_zones,
                                                        cleared_cacheback_cache):
    job = DocumentNearestZoneJob()

    top_doc = doc_hierarchy_with_zones.top
    middle_top_doc = doc_hierarchy_with_zones.middle_top
    middle_bottom_doc = doc_hierarchy_with_zones.middle_bottom
    bottom_doc = doc_hierarchy_with_zones.bottom

    top_zone = top_doc.zone
    middle_top_zone = middle_top_doc.zone

    # Load the cache for each of the docs.
    assert job.get(top_doc.pk) == top_zone
    assert job.get(middle_top_doc.pk) == middle_top_zone
    assert job.get(middle_bottom_doc.pk) == middle_top_zone
    assert job.get(bottom_doc.pk) == middle_top_zone

    # Change and save the document id field on a zone.
    assert middle_top_zone.document == middle_top_doc
    with mock.patch('kuma.wiki.jobs.DocumentNearestZoneJob.refresh',
                    wraps=job.refresh) as mock_refresh:
        middle_top_zone.document = bottom_doc
        middle_top_zone.save()

    # The cache for the middle-top doc and its descendants should have been
    # invalidated.
    assert job.get(middle_top_doc.pk) == top_zone
    assert job.get(middle_bottom_doc.pk) == top_zone
    assert job.get(bottom_doc.pk) == middle_top_zone

    assert mock_refresh.call_count == 3
    mock_refresh.assert_has_calls([
        mock.call(middle_top_doc.pk),
        mock.call(middle_bottom_doc.pk),
        mock.call(bottom_doc.pk)
    ], any_order=True)


def test_nearest_zone_cache_invalidation_on_zone_delete(doc_hierarchy_with_zones,
                                                        cleared_cacheback_cache):
    job = DocumentNearestZoneJob()

    top_doc = doc_hierarchy_with_zones.top
    middle_top_doc = doc_hierarchy_with_zones.middle_top
    middle_bottom_doc = doc_hierarchy_with_zones.middle_bottom
    bottom_doc = doc_hierarchy_with_zones.bottom

    top_zone = top_doc.zone
    middle_top_zone = middle_top_doc.zone

    # Load the cache for each of the docs.
    assert job.get(top_doc.pk) == top_zone
    assert job.get(middle_top_doc.pk) == middle_top_zone
    assert job.get(middle_bottom_doc.pk) == middle_top_zone
    assert job.get(bottom_doc.pk) == middle_top_zone

    # Delete a zone.
    with mock.patch('kuma.wiki.jobs.DocumentNearestZoneJob.refresh',
                    wraps=job.refresh) as mock_refresh:
        middle_top_zone.delete()

    # The cache for the top doc and its descendants should have been invalidated.
    assert job.get(top_doc.pk) == top_zone
    assert job.get(middle_top_doc.pk) == top_zone
    assert job.get(middle_bottom_doc.pk) == top_zone
    assert job.get(bottom_doc.pk) == top_zone

    assert mock_refresh.call_count == 3
    mock_refresh.assert_has_calls([
        mock.call(middle_top_doc.pk),
        mock.call(middle_bottom_doc.pk),
        mock.call(bottom_doc.pk),
    ], any_order=True)


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
