"""Tests for the DocumentCurrentSource class (document.current_revision)."""


from unittest import mock

from . import mock_storage
from ..sources import DocumentCurrentSource


def test_gather_has_current(root_doc):
    """If document.current_revision is set, we're done."""
    storage = mock_storage(spec=['get_document'])
    storage.get_document.return_value = root_doc
    source = DocumentCurrentSource(root_doc.get_absolute_url())

    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES


def test_gather_needs_to_scrape_history(root_doc):
    """If the document history is unavailable, wait."""
    root_doc.current_revision = None
    root_doc.save()
    root_url = root_doc.get_absolute_url()
    storage = mock_storage(spec=['get_document', 'get_document_history'])
    storage.get_document.return_value = root_doc
    storage.get_document_history.return_value = None
    source = DocumentCurrentSource(root_url)

    resources = source.gather(None, storage)
    assert resources == [('document_history', root_url, {'revisions': 1})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN
    storage.get_document_history.assert_called_once_with(root_doc.locale,
                                                         root_doc.slug)


def test_gather_needs_to_scrape_revision(root_doc):
    """If a revision was requested but not scraped, wait."""
    root_doc.current_revision = None
    root_doc.save()
    rev1, rev2 = root_doc.revisions.all()
    storage = mock_storage(spec=['get_document', 'get_document_history',
                                 'get_revision'])
    storage.get_document.return_value = root_doc
    storage.get_document_history.return_value = {
        'is_all': False,
        'revisions': [
            ('revision', rev1.get_absolute_url(), {}),
            ('revision', rev2.get_absolute_url(), {})]}
    storage.get_revision.return_value = None
    source = DocumentCurrentSource(root_doc.get_absolute_url())

    resources = source.gather(None, storage)
    assert resources == [('revision', rev1.get_absolute_url(), {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN
    storage.get_revision.assert_called_once_with(rev1.id)


def test_gather_needs_to_scrape_more_revisions(root_doc):
    """If a revision was included in history but not scraped, request it."""
    root_doc.current_revision = None
    root_doc.save()
    rev1, rev2 = root_doc.revisions.all()
    storage = mock_storage(spec=['get_document', 'get_document_history',
                                 'get_revision'])
    storage.get_document.return_value = root_doc
    storage.get_document_history.return_value = {
        'is_all': False,
        'revisions': [
            ('revision', rev1.get_absolute_url(), {}),
            ('revision', rev2.get_absolute_url(), {})]}
    storage.get_revision.return_value = rev1
    source = DocumentCurrentSource(root_doc.get_absolute_url())

    resources = source.gather(None, storage)
    assert resources == [
        ('document', '/en-US/docs/Root', {'revisions': 2}),
        ('revision', rev2.get_absolute_url(), {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN
    storage.get_revision.assert_called_once_with(rev1.id)


def test_gather_needs_to_scrape_more_history(root_doc):
    """If we've scraped all the known revisions, request more history."""
    root_doc.current_revision = None
    root_doc.save()
    root_url = root_doc.get_absolute_url()
    rev1, rev2 = root_doc.revisions.all()
    storage = mock_storage(spec=['get_document', 'get_document_history',
                                 'get_revision'])
    storage.get_document.return_value = root_doc
    storage.get_document_history.return_value = {
        'is_all': False,
        'revisions': [
            ('revision', rev1.get_absolute_url(), {}),
            ('revision', rev2.get_absolute_url(), {})]}
    storage.get_revision.return_value = rev1
    source = DocumentCurrentSource(root_url, revisions=2)

    resources = source.gather(None, storage)
    assert resources == [
        ('document', root_url, {'revisions': 3}),
        ('document_history', root_url, {'revisions': 4})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN
    assert storage.get_revision.mock_calls == [
        mock.call(rev1.id), mock.call(rev2.id)]


def test_gather_no_more_history_to_scrape(root_doc):
    """If a doc has no current rev, scrape all history and fail."""
    root_doc.current_revision = None
    root_doc.save()
    root_url = root_doc.get_absolute_url()
    rev1, rev2 = root_doc.revisions.all()
    storage = mock_storage(spec=['get_document', 'get_document_history',
                                 'get_revision'])
    storage.get_document.return_value = root_doc
    storage.get_document_history.return_value = {
        'is_all': True,
        'revisions': [
            ('revision', rev1.get_absolute_url(), {}),
            ('revision', rev2.get_absolute_url(), {})]}
    storage.get_revision.return_value = rev1
    source = DocumentCurrentSource(root_url, revisions=2)

    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_UNKNOWN
