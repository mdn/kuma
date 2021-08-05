import datetime

import pytest
from django.utils import timezone

from kuma.documenturls.models import DocumentURL, DocumentURLCheck
from kuma.documenturls.tasks import refresh_document_urls


@pytest.mark.django_db
def test_happy_path_refresh(mock_requests, settings):

    # Create 4 DocumentURL rows.
    # One that shouldn't need to be refreshed.
    # One that's been refresh at least once before.
    # One that will 404
    # One that will 5xx
    # One that will perfectly 200 and be updated with new metadata

    a = DocumentURL.objects.create(
        uri="/en-US/docs/A",
        absolute_url=f"{settings.BOOKMARKS_BASE_URL}/en-US/docs/A/index.json",
        metadata={
            "title": "Old A",
        },
    )
    b = DocumentURL.objects.create(
        uri="/en-US/docs/B",
        absolute_url=f"{settings.BOOKMARKS_BASE_URL}/en-US/docs/B/index.json",
        metadata={
            "title": "Old B",
        },
    )
    DocumentURL.objects.create(
        uri="/en-US/docs/C",
        absolute_url=f"{settings.BOOKMARKS_BASE_URL}/en-US/docs/C/index.json",
        metadata={
            "title": "Old C",
        },
    )
    d = DocumentURL.objects.create(
        uri="/en-US/docs/D",
        absolute_url=f"{settings.BOOKMARKS_BASE_URL}/en-US/docs/D/index.json",
        metadata={
            "title": "Old D",
        },
    )
    # Move the 'modified' datetime of 'a' and 'b' back in time.
    DocumentURL.objects.filter(id__in=[a.id, b.id, d.id]).update(
        modified=timezone.now()
        - datetime.timedelta(seconds=settings.REFRESH_DOCUMENTURLS_MIN_AGE_SECONDS + 1)
    )
    # Store these so we can compare afterwards
    a_modified = DocumentURL.objects.get(id=a.id).modified
    b_modified = DocumentURL.objects.get(id=b.id).modified
    d_modified = DocumentURL.objects.get(id=d.id).modified

    # Pretend 'b' has been checked before
    DocumentURLCheck.objects.create(document_url=b, http_error=200, headers={})

    mock_requests.register_uri(
        "GET",
        settings.BOOKMARKS_BASE_URL + "/en-US/docs/A/index.json",
        json={"doc": {"title": "New A", "mdn_url": "/en-US/docs/A"}},
    )
    mock_requests.register_uri(
        "GET",
        settings.BOOKMARKS_BASE_URL + "/en-US/docs/B/index.json",
        text="Not Found",
        status_code=404,
    )
    mock_requests.register_uri(
        "GET",
        settings.BOOKMARKS_BASE_URL + "/en-US/docs/D/index.json",
        text="Bad Gateway",
        status_code=504,
    )
    # Note that we never set up a mock request for /en-US/docs/C/index.json
    # because it won't even be attempted.

    refresh_document_urls()

    a.refresh_from_db()
    assert a.metadata["title"] == "New A"
    assert not a.invalid
    assert a.modified > a_modified

    b.refresh_from_db()
    assert b.invalid
    assert b.modified > b_modified

    d.refresh_from_db()
    assert not d.invalid
    assert d.modified == d_modified
