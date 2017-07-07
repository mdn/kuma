# -*- coding: utf-8 -*-
"""Tests for the DocumentSource class."""
from __future__ import unicode_literals
from datetime import datetime

from kuma.scrape.sources import DocumentSource
from . import mock_storage


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
    'is_zone_root': False,
    'locale': 'en-US',
    'modified': datetime(2016, 11, 8, 15, 26, 23, 807948),
    'slug': 'Test',
    'tags': [],
    'title': 'Test Title',
    'uuid': 'f9f8e807-a98e-4106-867f-4e1c99cb7f2c',
    'zone_css_slug': '',
}


def test_gather_root_no_prereqs():
    doc_path = '/en-US/docs/RootDoc'
    source = DocumentSource(doc_path)
    storage = mock_storage(spec=['get_document', 'get_document_rendered'])
    resources = source.gather(None, storage)
    assert resources == [('document_rendered', doc_path, {})]
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
    storage = mock_storage(spec=['get_document', 'get_document_rendered'])
    storage.get_document.return_value = "existing document"
    resources = source.gather(None, storage)
    assert resources == [('document_rendered', doc_path, {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_child_doc():
    """A child document requires the parent document."""
    parent_path = '/en-US/docs/Root'
    child_path = parent_path + '/Child'
    source = DocumentSource(child_path)
    storage = mock_storage(spec=['get_document', 'get_document_rendered'])
    resources = source.gather(None, storage)
    assert resources == [
        ('document', parent_path, {}),
        ('document_rendered', child_path, {})]
    assert source.state == source.STATE_PREREQ


def test_gather_child_doc_parent_in_storage():
    """If the parent document is available, it is not requested."""
    parent_path = '/en-US/docs/Root'
    child_path = parent_path + '/Child'
    source = DocumentSource(child_path, force=True)
    storage = mock_storage(spec=['get_document', 'get_document_rendered'])
    storage.get_document.return_value = 'parent document'
    resources = source.gather(None, storage)
    assert resources == [('document_rendered', child_path, {})]
    storage.get_document.assert_called_once_with('en-US', 'Root')
    assert source.state == source.STATE_PREREQ


def test_gather_standard_doc():
    """If the rendered document is standard, get next resources."""
    path = '/en-US/docs/RootDoc'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_rendered', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_rendered.return_value = {}
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_rendered.return_value = {}  # Standard doc
    storage.get_document_metadata.return_value = {}  # Empty for now
    storage.get_document_history.return_value = []   # No history
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_gather_standard_doc_all_prereqs():
    path = '/en-US/docs/Test'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {}  # Standard doc
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {}  # Standard doc
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_rendered.return_value = {}  # Standard doc
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {}  # Standard doc
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


def test_gather_zoned_doc_init():
    """A zone URL requests the zone doc."""
    path = '/en-US/Zone'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=['get_zone_root'])
    resources = source.gather(None, storage)
    assert resources == [('zone_root', path, {})]
    assert source.state == source.STATE_PREREQ


def test_gather_zoned_doc_error():
    """If the zoned document fails (isn't a zone), then the doc errors too."""
    path = '/en-US/Zone'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=['get_zone_root'])
    storage.get_zone_root.return_value = {'errors': ['failed']}
    resources = source.gather(None, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR


def test_gather_zoned_doc_is_normalized():
    """The zoned doc is used to normalize the URL."""
    path = '/en-US/Zone'
    source = DocumentSource(path, force=True)
    assert not source.normalized_path
    assert not source.locale
    assert not source.slug
    storage = mock_storage(spec=[
        'get_zone_root', 'get_document', 'get_document_rendered'])
    storage.get_zone_root.return_value = {
        'zone_path': path, 'doc_path': '/en-US/docs/Root/Zone'}
    resources = source.gather(None, storage)
    assert resources == [
        ('document', '/en-US/docs/Root', {}),
        ('document_rendered', '/en-US/docs/Root/Zone', {})]
    assert source.state == source.STATE_PREREQ
    assert source.normalized_path == '/en-US/docs/Root/Zone'
    assert source.locale == 'en-US'
    assert source.slug == 'Root/Zone'


def test_gather_normalized_path_moved_page_needed():
    """If a document is a redirect, request the target page."""
    source = DocumentSource('/en-US/docs/Origin', force=True)
    storage = mock_storage(spec=['get_document', 'get_document_rendered'])
    storage.get_document_rendered.return_value = {
        'redirect_to': '/en-US/docs/NewLocation'}
    resources = source.gather(None, storage)
    assert resources == [
        ('document', '/en-US/docs/NewLocation', {})]
    storage.get_document.assert_called_once_with('en-US', 'NewLocation')
    assert source.state == source.STATE_PREREQ


def test_gather_normalized_path_moved_page_followed():
    """If a document is a redirect to a normal page, create a redirect."""
    source = DocumentSource('/en-US/docs/Origin', force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_rendered', 'save_document'])
    storage.get_document_rendered.return_value = {
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


def test_gather_redirect_to_zone_page_first_pass():
    """If a document is a redirect to a zone, request the zone root."""
    parent_path = '/en-US/docs/Root'
    path = parent_path + '/Zone'
    zone_path = '/en-US/Zone'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_rendered', 'get_zone_root',
        'get_document_metadata', 'get_document_history'])
    storage.get_document_rendered.return_value = {'redirect_to': zone_path}
    resources = source.gather(None, storage)
    assert resources == [
        ('document', parent_path, {}),
        ('zone_root', zone_path, {}),
        ('document_meta', path, {'force': True}),
        ('document_history', path, {'revisions': 1})]
    assert source.state == source.STATE_PREREQ


def test_gather_redirect_to_errored_zone_page_is_error():
    """If a document is a redirect to an errored zone, doc is also errored."""
    parent_path = '/en-US/docs/Root'
    path = parent_path + '/Zone'
    zone_path = '/en-US/Zone'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_rendered', 'get_zone_root',
        'get_document_metadata', 'get_document_history'])
    storage.get_document_rendered.return_value = {'redirect_to': zone_path}
    storage.get_zone_root.return_value = {'errors': 'bad zone'}
    source.gather(None, storage)
    assert source.state == source.STATE_ERROR


def test_gather_redirect_to_zone_page_complete():
    """A zoned document has more data passed to storage.save_document()"""
    parent_path = '/en-US/docs/Root'
    path = parent_path + '/Zone'
    zone_path = '/en-US/Zone'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_rendered', 'get_zone_root',
        'get_document_metadata', 'get_document_history', 'save_document'])
    storage.get_document.return_value = 'Root doc'
    storage.get_document_rendered.return_value = {'redirect_to': zone_path}
    storage.get_zone_root.return_value = {
        'doc_path': path,
        'zone_path': zone_path}
    metadata = doc_metadata.copy()
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2017', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_current', path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    expected = doc_data.copy()
    expected['slug'] = 'Root/Zone'
    expected['parent_topic'] = 'Root doc'
    expected['zone_redirect_path'] = zone_path
    assert storage.save_document.call_count == 1
    assert storage.save_document.call_args[0][0] == expected  # Better diff
    storage.save_document.assert_called_once_with(expected)


def test_gather_redirect_to_zone_subpage():
    """If a document is a redirect to zone subpage, request the zone root."""
    parent_path = '/en-US/docs/Root/Zone'
    path = parent_path + '/Child'
    zone_root_path = '/en-US/Zone'
    zone_path = zone_root_path + '/Child'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_rendered', 'get_zone_root',
        'get_document_metadata', 'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {'redirect_to': zone_path}
    storage.get_zone_root.return_value = {
        'doc_path': parent_path, 'zone_path': zone_root_path}
    resources = source.gather(None, storage)
    assert resources == [
        ('document', parent_path, {}),  # Parerent of current page
        ('document', parent_path, {}),  # zone_path from zone root
        ('document_meta', path, {'force': True}),
        ('document_history', path, {'revisions': 1}),
    ]
    assert source.state == source.STATE_PREREQ


def test_gather_redirect_to_zone_subpage_complete():
    """A zoned subpage has more data passed to storage.save_document()"""
    parent_path = '/en-US/docs/Root/Zone'
    path = parent_path + '/Child'
    zone_root_path = '/en-US/Zone'
    zone_path = zone_root_path + '/Child'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document', 'get_document_rendered', 'get_zone_root',
        'get_document_metadata', 'get_document_history', 'save_document'])
    storage.get_document.return_value = 'Root doc'
    storage.get_document_rendered.return_value = {'redirect_to': zone_path}
    storage.get_zone_root.return_value = {
        'doc_path': parent_path, 'zone_path': '/en-US/Zone'}
    metadata = doc_metadata.copy()
    storage.get_document_metadata.return_value = metadata
    storage.get_document_history.return_value = [
        ('revisions', path + '$revision/2018', {})]
    resources = source.gather(None, storage)
    assert resources == [('document_current', path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    expected = doc_data.copy()
    expected['slug'] = 'Root/Zone/Child'
    expected['parent_topic'] = 'Root doc'
    expected['zone_redirect_path'] = zone_root_path
    assert storage.save_document.call_count == 1
    assert storage.save_document.call_args[0][0] == expected  # Better diff
    storage.save_document.assert_called_once_with(expected)


def test_gather_localized_doc_without_metadata():
    """A localized document will wait for metadata."""
    path = '/fr/docs/Racine'
    source = DocumentSource(path, force=True)
    storage = mock_storage(spec=[
        'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {}
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
        'get_document', 'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {}
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history'])
    storage.get_document_rendered.return_value = {}
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
        'get_document', 'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'save_document'])
    storage.get_document_rendered.return_value = {}
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'get_document_children', 'save_document'])
    storage.get_document_rendered.return_value = {}  # Standard doc
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
        'get_document_rendered', 'get_document_metadata',
        'get_document_history', 'get_document_children', 'save_document'])
    storage.get_document_rendered.return_value = {}  # Standard doc
    storage.get_document_metadata.return_value = doc_metadata
    storage.get_document_history.return_value = [
        ('revisions', doc_path + '$revision/2016', {})]
    storage.get_document_children.return_value = []
    resources = source.gather(None, storage)
    assert resources == [('document_current', doc_path, {'revisions': 1})]
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
