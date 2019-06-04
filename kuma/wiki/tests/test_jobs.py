from datetime import datetime

import pytest

from ..jobs import DocumentContributorsJob
from ..models import Revision


@pytest.mark.parametrize("mode", ["maintenance-mode", "normal-mode"])
def test_contributors(db, cleared_cacheback_cache, settings, wiki_user_3,
                      root_doc_with_mixed_contributors, mode):
    """
    Tests basic operation, ordering, caching, and handling of banned and
    inactive contributors.
    """
    from kuma.celery import app
    assert app.conf['task_always_eager'], 'task_always_eager'

    # mode="normal-mode" # TEMP
    settings.MAINTENANCE_MODE = (mode == "maintenance-mode")

    fixture = root_doc_with_mixed_contributors
    root_doc = fixture.doc

    job = DocumentContributorsJob()
    # Set this to true so we bypass the Celery task queue.
    job.fetch_on_miss = True
    # This will force
    # job.fetch_on_stale_threshold = 0#job.lifetime + job.refresh_timeout - 1
    contributors = job.get(root_doc.pk)

    if settings.MAINTENANCE_MODE:
        assert not contributors
        return

    valid_contrib_ids = [user.pk for user in fixture.contributors.valid]
    # Banned and inactive contributors should not be included.
    assert [c['id'] for c in contributors] == valid_contrib_ids

    banned_user = fixture.contributors.banned.user

    # Delete the ban.
    from django.core.cache import cache
    # print(dir(cache))
    cache_keys_before = cache.keys('*')
    fixture.contributors.banned.ban.delete()
    cache_keys_after = cache.keys('*')
    # assert len(cache_keys_after) < len(cache_keys_before), "CACHE DIDN'T REDUCE!"
    # print("CACHE KEYS AFTER:")
    # print(cache.keys('*'))

    # The freshly un-banned user is now among the contributors because the
    # cache has been invalidated.

    contributors = job.get(root_doc.pk)
    got = set(c['id'] for c in contributors)
    assert banned_user.pk in got

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
    contributors = job.get(root_doc.pk)
    print("CONTRIBUTORS 3:", [x['id'] for x in contributors])
    assert ([c['id'] for c in job.get(root_doc.pk)] ==
            ([wiki_user_3.pk, banned_user.pk] + valid_contrib_ids))


    assert 0
