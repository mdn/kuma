# -*- coding: utf-8 -*-
"""Tests for the RevisionSource class ($revision/ID API)."""
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
import mock
import pytest

from kuma.wiki.models import Document, Revision

from . import mock_requester, mock_storage
from ..sources import RevisionSource


@pytest.fixture
def tagged_doc(db, django_user_model):
    """A root document with one tagged revision."""
    document = Document.objects.create(
        locale='en-US', slug='Test', title='Test Document')
    creator = django_user_model.objects.create(username='creator')
    revision = Revision.objects.create(
        content='<p>The HTML element <code>&lt;input&gt;</code>...',
        comment='Frist Post!',
        creator=creator,
        created=datetime(2016, 12, 15, 17, 23),
        document=document,
        title='Test Document',
        tags='"One" "Two" "Three"'
    )
    assert document.current_revision == revision
    return document


def test_invalid_path():
    """A bad revision path is detected at initialization."""
    source = RevisionSource('/bad/path')
    assert source.state == source.STATE_ERROR


def test_gather_no_prereqs(tagged_doc, client):
    """On the first call, multiple items are requested from storage."""
    doc_path = tagged_doc.get_absolute_url()
    rev_path = doc_path + '$revision/%d' % tagged_doc.current_revision_id
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    source = RevisionSource(rev_path)
    requester = mock_requester(content=html)
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'save_revision_html', 'get_user'])
    resources = source.gather(requester, storage)
    assert resources == [
        ('document', doc_path, {}),
        ('document_meta', doc_path, {}),
        ('user', 'creator', {})
    ]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN
    storage.save_revision_html.assert_called_once_with(rev_path, html)


def test_gather_existing_rev_and_doc():
    """If prereqs are present then source is done."""
    doc_path = '/en-US/docs/Test'
    rev_path = doc_path + '$revision/100'
    source = RevisionSource(rev_path)
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=['get_document', 'get_revision'])
    storage.get_document.return_value = "existing"
    revision = mock.Mock(spec_set=['document'])
    revision.document = "existing"
    storage.get_revision.return_value = revision

    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_NO
    storage.get_document.assert_called_once_with('en-US', 'Test')
    storage.get_revision.assert_called_once_with(100)


def test_gather_existing_doc(tagged_doc, client):
    """If only the doc is present, then full gather is performed."""
    doc_path = tagged_doc.get_absolute_url()
    rev_path = doc_path + '$revision/%d' % tagged_doc.current_revision_id
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    source = RevisionSource(rev_path)
    requester = mock_requester(content=html)
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'save_revision_html', 'get_user'])
    storage.get_document.return_value = tagged_doc
    resources = source.gather(requester, storage)
    assert resources == [
        ('document_meta', doc_path, {}),
        ('user', 'creator', {})
    ]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN
    storage.save_revision_html.assert_called_once_with(rev_path, html)


def test_gather_doc_mismatch_is_error():
    """If stored doc does not agree with stored revision doc, then error."""
    doc_path = '/en-US/docs/Test'
    rev_path = doc_path + '$revision/100'
    source = RevisionSource(rev_path)
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=['get_document', 'get_revision'])
    doc1 = mock.Mock(spec_set=['get_absolute_url'])
    doc1.get_absolute_url.return_value = '/en-US/docs/Foo'
    doc2 = mock.Mock(spec_set=['get_absolute_url'])
    doc2.get_absolute_url.return_value = '/en-US/docs/Test'
    storage.get_document.return_value = doc1
    revision = mock.Mock(spec_set=['document'])
    revision.document = doc2
    storage.get_revision.return_value = revision

    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_NO
    storage.get_document.assert_called_once_with('en-US', 'Test')
    storage.get_revision.assert_called_once_with(100)


def test_gather_with_prereqs(tagged_doc, client):
    """On the first call, multiple items are requested from storage."""
    doc_path = tagged_doc.get_absolute_url()
    rev_path = doc_path + '$revision/%d' % tagged_doc.current_revision_id
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    source = RevisionSource(rev_path)
    source.state = source.STATE_PREREQ
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'get_user', 'save_revision'])
    storage.get_document.return_value = tagged_doc
    storage.get_document_metadata.return_value = {'is_meta': True}
    storage.get_revision_html.return_value = html
    storage.get_user.return_value = {'username': 'creator'}
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    expected_data = {
        'id': tagged_doc.current_revision_id,
        'comment': 'Frist Post!',
        'content': '<p>The HTML element <code>&lt;input&gt;</code>...</p>',
        'created': datetime(2016, 12, 15, 17, 23),
        'creator': {'username': 'creator'},
        'document': tagged_doc,
        'is_current': True,
        'localization_tags': [],
        'review_tags': [],
        'slug': 'Test',
        'tags': ['One', 'Three', 'Two'],
        'title': 'Test Document',
    }
    storage.save_revision.assert_called_once_with(expected_data)


def test_gather_second_pass(tagged_doc, client):
    """A revision will request a document on the second pass."""
    doc_path = tagged_doc.get_absolute_url()
    rev_path = doc_path + '$revision/%d' % tagged_doc.current_revision_id
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    source = RevisionSource(rev_path)
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'get_user', 'save_revision'])
    storage.get_document.return_value = None
    storage.get_document_metadata.return_value = {'is_meta': True}
    storage.get_revision_html.return_value = html
    storage.get_user.return_value = {'username': 'creator'}

    # First pass, document is not available from storage (None twice)
    resources = source.gather(requester, storage)
    assert resources == [('document', doc_path, {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN

    # Second pass, document is available from storage
    storage.get_document.return_value = tagged_doc
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    expected_data = {
        'id': tagged_doc.current_revision_id,
        'comment': 'Frist Post!',
        'content': '<p>The HTML element <code>&lt;input&gt;</code>...</p>',
        'created': datetime(2016, 12, 15, 17, 23),
        'creator': {'username': 'creator'},
        'document': tagged_doc,
        'is_current': True,
        'localization_tags': [],
        'review_tags': [],
        'slug': 'Test',
        'tags': ['One', 'Three', 'Two'],
        'title': 'Test Document',
    }
    storage.save_revision.assert_called_once_with(expected_data)


def test_gather_document_slug_wins(tagged_doc, client):
    """
    If the document slug is different from the revision, doc wins.

    This appears to be common around page moves.
    """
    orig_doc_path = tagged_doc.get_absolute_url()
    orig_rev_path = orig_doc_path + ('$revision/%d' %
                                     tagged_doc.current_revision_id)
    html = client.get(orig_rev_path, HTTP_HOST=settings.WIKI_HOST).content
    tagged_doc.slug = 'Other'
    doc_path = tagged_doc.get_absolute_url()
    rev_path = doc_path + '$revision/%d' % tagged_doc.current_revision_id
    source = RevisionSource(rev_path)
    source.state = source.STATE_PREREQ
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'get_user', 'save_revision'])
    storage.get_document.return_value = tagged_doc
    storage.get_document_metadata.return_value = {'is_meta': True}
    storage.get_revision_html.return_value = html
    storage.get_user.return_value = {'username': 'creator'}
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    expected_data = {
        'id': tagged_doc.current_revision_id,
        'comment': 'Frist Post!',
        'content': '<p>The HTML element <code>&lt;input&gt;</code>...</p>',
        'created': datetime(2016, 12, 15, 17, 23),
        'creator': {'username': 'creator'},
        'document': tagged_doc,
        'is_current': True,
        'localization_tags': [],
        'review_tags': [],
        'slug': 'Other',
        'tags': ['One', 'Three', 'Two'],
        'title': 'Test Document',
    }
    storage.save_revision.assert_called_once_with(expected_data)


def test_gather_older_revision(root_doc, client):
    """Older revisions can be imported without some tags."""
    doc_path = root_doc.get_absolute_url()
    old_rev = root_doc.revisions.order_by('id')[0]
    assert old_rev != root_doc.current_revision
    rev_path = doc_path + '$revision/%d' % old_rev.id
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    source = RevisionSource(rev_path)
    source.state = source.STATE_PREREQ
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'get_user', 'save_revision'])
    storage.get_document.return_value = root_doc
    storage.get_document_metadata.return_value = {'is_meta': True}
    storage.get_revision_html.return_value = html
    storage.get_user.return_value = {'username': 'creator'}
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    # Missing review and localization tags if it is not the current revision
    expected_data = {
        'id': old_rev.id,
        'comment': '',
        'content': '<p>Getting started...</p>',
        'created': datetime(2016, 1, 1),
        'creator': {'username': 'creator'},
        'document': root_doc,
        'is_current': False,
        'slug': 'Root',
        'tags': [],
        'title': 'Root Document',
    }
    storage.save_revision.assert_called_once_with(expected_data)


def test_gather_missing_revision_is_error(tagged_doc):
    """If the revision HTML can't be fetched, the source is errored."""
    doc_path = tagged_doc.get_absolute_url()
    rev_path = doc_path + '$revision/%s' % tagged_doc.current_revision_id
    source = RevisionSource(rev_path)
    requester = mock_requester(status_code=404)
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_based_on_is_needed(translated_doc, client):
    """If a based_on revision is specified, it is required."""
    rev = translated_doc.current_revision
    rev_path = rev.get_absolute_url()
    based_on_path = rev.based_on.get_absolute_url()
    source = RevisionSource(rev_path, based_on=based_on_path)
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'get_user', 'save_revision'])
    storage.get_document.return_value = translated_doc
    storage.get_document_metadata.return_value = {'is_meta': True}
    storage.get_revision_html.return_value = html
    storage.get_user.return_value = {'username': 'creator'}
    resources = source.gather(requester, storage)
    assert resources == [('revision', based_on_path, {})]
    assert source.state == source.STATE_PREREQ
    assert source.freshness == source.FRESH_UNKNOWN


def test_gather_based_on_is_available(translated_doc, client):
    """If a based_on revision is specified and available, it is used."""
    rev = translated_doc.current_revision
    rev_path = rev.get_absolute_url()
    based_on_path = rev.based_on.get_absolute_url()
    source = RevisionSource(rev_path, based_on=based_on_path)
    html = client.get(rev_path, HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(requester_spec=[])
    storage = mock_storage(spec=[
        'get_document', 'get_revision', 'get_document_metadata',
        'get_revision_html', 'get_user', 'save_revision'])
    storage.get_document.return_value = translated_doc
    storage.get_document_metadata.return_value = {'is_meta': True}
    storage.get_revision_html.return_value = html
    storage.get_user.return_value = {'username': 'creator'}
    # First call is for this revision, return None to scrape
    # Second call is for the based_on revision, return it
    storage.get_revision.side_effect = [None, rev.based_on]
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_DONE
    assert source.freshness == source.FRESH_YES
    expected_data = {
        'id': rev.id,
        'based_on_id': rev.based_on.id,
        'comment': 'Root Racine',
        'content': '<p>Commencer...</p>',
        'created': datetime(2017, 6, 1, 15, 28),
        'creator': {'username': 'creator'},
        'document': translated_doc,
        'is_current': True,
        'localization_tags': [],
        'review_tags': [],
        'slug': 'Racine',
        'tags': [],
        'title': 'Document Racine',
    }
    storage.save_revision.assert_called_once_with(expected_data)
