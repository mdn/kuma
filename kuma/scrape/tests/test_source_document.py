# -*- coding: utf-8 -*-
"""Tests for the DocumentSource class."""


from datetime import datetime

from . import mock_storage
from ..sources import DocumentSource


# Basic metadata for a Document
doc_metadata = {
    # Omitted: json_modified, label, last_edit, etc.
    'id': 100,
    'locale': 'en-US',
    'localization_tags': [],
    'modified': '2016-11-08T15:26:23.807948',
    'review_tags': [],
    'slug': 'Test',
    'tags': [],
    'title': 'Test Title',
    'translations': [],
    'url': '/en-US/docs/Test',
    'uuid': 'f9f8e807-a98e-4106-867f-4e1c99cb7f2c',
}

# The data passed to Storage.save_document for this metadata
doc_data = {
    'id': 100,
    'locale': 'en-US',
    'modified': datetime(2016, 11, 8, 15, 26, 23, 807948),
    'slug': 'Test',
    'tags': [],
    'title': 'Test Title',
    'uuid': 'f9f8e807-a98e-4106-867f-4e1c99cb7f2c',
}


def test_gather_root_no_prereqs():
    doc_path = '/en-US/docs/RootDoc'
    source = DocumentSource(doc_path)
    storage = mock_storage(spec=['get_document', 'get_document_redirect'])
    resources = source.gather(None, storage)
    assert resources == [('document_redirect', doc_path, {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_document_in_storage():
    """If the Document already exists, short-circuit downloads."""
    source = DocumentSource('/en-US/docs/Root/Child')
    storage = mock_storage(spec=['get_document'])
    storage.get_document.return_value = "existing document"
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO


def test_gather_forced():
    """Resources are fetched if force=True."""
    doc_path = '/en-US/docs/RootDoc'
    source = DocumentSource(doc_path, force=True)
    storage = mock_storage(spec=['get_document', 'get_document_redirect'])
    storage.get_document.return_value = "existing document"
    resources = source.gather(None, storage)
    assert resources == [('document_redirect', doc_path, {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_child_doc():
    """A child document requires the parent document."""
    parent_path = '/en-US/docs/Root'
    child_path = parent_path + '/Child'
    source = DocumentSource(child_path)
    storage = mock_storage(spec=['get_document', 'get_document_redirect'])
    resources = source.gather(None, storage)
    assert resources == [
        ('document', parent_path, {}),
        ('document_redirect', child_path, {})]
    assert source.state == source.STATE_PREREQ


def test_gather_child_doc_parent_in_storage():
    """If the parent document is available, it is not requested."""
    parent_path = '/en-US/docs/Root'
    child_path = parent_path + '/Child'
    source = DocumentSource(child_path, force=True)
    storage = mock_storage(spec=['get_document', 'get_document_redirect'])
    storage.get_document.return_value = 'parent document'
    resources = source.gather(None, storage)
    assert resources == [('document_redirect', child_path, {})]
    storage.get_document.assert_called_once_with('en-US', 'Root')
    assert source.state == source.STATE_PREREQ


def test_gather_standard_doc():
    """If the rendered document is standard, get next resources."""
    path = '/en-US/docs/RootDoc'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_redirect.return_value = {}
    resources = source.gather(None, storage)
    assert resources == [
        ('document_meta', path, {'force': True}),
        ('document_history', path, {'revisions': 1})]
    assert source.state == source.STATE_PREREQ
    storage.get_document_metadata.assert_called_once_with('en-US', 'RootDoc')
    storage.get_document_history.assert_called_once_with('en-US', 'RootDoc')


def test_gather_standard_doc_empty_history_is_error():
    path = '/en-US/docs/RootDoc'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    storage.get_document_metadata.return_value = {}  # Empty for now
    storage.get_document_history.return_value = []   # No history
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_gather_document_zone_url_is_error():
    """Old vanity zone URLs are not loaded."""
    doc_path = "/en-US/Firefox/Releases/22"
    source = DocumentSource(doc_path)
    storage = mock_storage(spec=[])  # Storage is skipped
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_standard_doc_all_prereqs():
    path = '/en-US/docs/Test'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    storage.get_document_metadata.return_value = doc_metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2016', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_current', path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    storage.save_document.assert_called_once_with(doc_data)


def test_gather_standard_doc_metdata_loses():
    """If metadata doesn't match URL, use locale and slug from URL."""
    path = '/en-US/docs/Test'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    metadata = doc_metadata.copy()
    metadata['locale'] = 'EN-US'
    metadata['slug'] = 'TEST'
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2016', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_current', path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    storage.save_document.assert_called_once_with(doc_data)


def test_gather_standard_doc_bad_metadata():
    """If the metadata has an error, so does the document."""
    path = '/en-US/docs/Test'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    metadata = doc_metadata.copy()
    metadata['error'] = True
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2016', {})]
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_gather_standard_doc_no_uuid():
    path = '/en-US/docs/Test'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    metadata = doc_metadata.copy()
    del metadata['uuid']
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2016', {})]

    resources = source.gather(None, storage)
    assert resources == [('document_current', path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    expected = doc_data.copy()
    del expected['uuid']
    storage.save_document.assert_called_once_with(expected)


def test_gather_redirect_moved_page_needed():
    """If a document is a redirect, request the target page."""
    source = DocumentSource('/en-US/docs/Origin', force=True)
    storage = mock_storage(spec=['get_document', 'get_document_redirect'])
    storage.get_document_redirect.return_value = {
        'redirect_to': '/en-US/docs/NewLocation'}
    resources = source.gather(None, storage)
    assert resources == [
        ('document', '/en-US/docs/NewLocation', {})]
    storage.get_document.assert_called_once_with('en-US', 'NewLocation')
    assert source.state == source.STATE_PREREQ


def test_gather_redirect_moved_page_followed():
    """If a document is a redirect to a normal page, create a redirect."""
    source = DocumentSource('/en-US/docs/Origin', force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_redirect', 'save_document'])
    storage.get_document_redirect.return_value = {
        'redirect_to': '/en-US/docs/NewLocation'}
    storage.get_document.return_value = "Redirect Document"
    resources = source.gather(None, storage)
    assert resources == [('document_current', '/en-US/docs/Origin',
                          {'revisions': 1})]
    assert source.state == source.STATE_DONE
    expected_data = {
        'locale': 'en-US',
        'slug': 'Origin',
        'redirect_to': '/en-US/docs/NewLocation'
    }
    storage.save_document.assert_called_once_with(expected_data)


def test_gather_localized_doc_without_metadata():
    """A localized document will wait for metadata."""
    path = '/fr/docs/Racine'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_redirect.return_value = {}
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2020', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_meta', path, {'force': True})]
    assert source.state == source.STATE_PREREQ


def test_gather_localized_doc_with_metadata():
    """A localized document will request the English document."""
    path = '/fr/docs/Racine'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_redirect.return_value = {}
    metadata = doc_metadata.copy()
    metadata['locale'] = 'fr'
    metadata['slug'] = 'Racine'
    metadata['url'] = path
    metadata['translations'] = [
        {'locale': 'es', 'url': '/es/docs/Raíz'},
        {'locale': 'en-US', 'url': '/en-US/docs/Root'},
    ]
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2020', {})]
    resources = source.gather(None, storage)
    assert resources == [('document', '/en-US/docs/Root', {})]
    assert source.state == source.STATE_PREREQ


def test_gather_localized_doc_invalid_english():
    """An invalid English document path is an error."""
    path = '/fr/docs/Racine'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_redirect.return_value = {}
    metadata = doc_metadata.copy()
    metadata['locale'] = 'fr'
    metadata['slug'] = 'Racine'
    metadata['url'] = path
    metadata['translations'] = [
        {'locale': 'en-US', 'url': '/en-US/ZoneRoot'},
    ]
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2020', {})]
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_gather_localized_doc_sets_parent():
    """A localized document will set the English document as parent."""
    path = '/fr/docs/Racine'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_redirect.return_value = {}
    metadata = doc_metadata.copy()
    metadata['locale'] = 'fr'
    metadata['slug'] = 'Racine'
    metadata['url'] = path
    metadata['translations'] = [
        {'locale': 'en-US', 'url': '/en-US/docs/Root'},
    ]
    storage.get_document.return_value = 'English document'
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2020', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_current', path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    expected = doc_data.copy()
    expected['locale'] = 'fr'
    expected['slug'] = 'Racine'
    expected['parent'] = 'English document'
    assert storage.save_document.call_count == 1
    assert storage.save_document.call_args[0][0] == expected  # Better diff
    storage.save_document.assert_called_once_with(expected)


def test_gather_document_children():
    """A depth > 0 will require the $children resource."""
    doc_path = '/en-US/docs/RootDoc'
    source = DocumentSource(doc_path, depth=1, force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'get_document_children', 'save_document'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    storage.get_document_metadata.return_value = doc_metadata
    storage.get_document_history.return_value = [
        ('revisions', doc_path + '$revision/2016', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_children', doc_path,
                          {'depth': 1, 'force': True})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_document_children_loaded():
    """If the $children resource is loaded, use it."""
    doc_path = '/en-US/docs/RootDoc'
    source = DocumentSource(doc_path, depth='all', force=True)
    storage = mock_storage(spec=[
        'get_document_redirect', 'get_document_metadata',
        'get_document_history', 'get_document_children', 'save_document'])
    storage.get_document_redirect.return_value = {}  # Standard doc
    storage.get_document_metadata.return_value = doc_metadata
    storage.get_document_history.return_value = [
        ('revisions', doc_path + '$revision/2016', {})]
    storage.get_document_children.return_value = []
    resources = source.gather(None, storage)
    assert resources == [('document_current', doc_path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
