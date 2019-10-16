# -*- coding: utf-8 -*-
"""Tests for the DocumentHistorySource class ($history API)."""
from __future__ import unicode_literals

from django.conf import settings

from . import mock_requester, mock_storage
from ..sources import DocumentHistorySource


def test_gather_revisions_default(root_doc, client):
    """The default is requests if revision count is unspecified."""
    path = root_doc.get_absolute_url()
    source = DocumentHistorySource(path)
    html = client.get(path + '$history', HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(content=html, status_code=200)
    storage = mock_storage(spec=[
        'get_document_history', 'save_document_history'])
    resources = source.gather(requester, storage)
    history_path = path + '$history'
    requester.request.assert_called_once_with(history_path,
                                              raise_for_status=False)
    rev1, rev2 = root_doc.revisions.all()
    revision_pattern = path + '$revision/%d'
    expected_resources = [
        ('revision', revision_pattern % rev.id, {}) for rev in [rev2]]
    assert resources == expected_resources
    assert source.state == source.STATE_DONE
    expected_data = {
        'is_all': False,
        'revisions': [
            ('revision', revision_pattern % rev2.id, {}),
            ('revision', revision_pattern % rev1.id, {})]}
    storage.save_document_history.assert_called_once_with(
        'en-US', 'Root', expected_data)


def test_gather_revisions_multiple(root_doc, client):
    """If a revision count is specified, that many are requested."""
    path = root_doc.get_absolute_url()
    source = DocumentHistorySource(path, revisions=2)
    html = client.get(path + '$history', HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(content=html, status_code=200)
    storage = mock_storage(spec=[
        'get_document_history', 'save_document_history'])
    resources = source.gather(requester, storage)
    history_path = path + '$history?limit=2'
    requester.request.assert_called_once_with(history_path,
                                              raise_for_status=False)
    rev1, rev2 = root_doc.revisions.all()
    revision_pattern = path + '$revision/%d'
    expected_resources = [
        ('revision', revision_pattern % rev.id, {}) for rev in [rev1, rev2]]
    assert resources == expected_resources
    assert source.state == source.STATE_DONE
    expected_data = {
        'is_all': False,
        'revisions': expected_resources[::-1]}
    storage.save_document_history.assert_called_once_with(
        'en-US', 'Root', expected_data)


def test_gather_revisions_more_than_available(root_doc, client):
    """If a revision count is more than the revisions, take note."""
    path = root_doc.get_absolute_url()
    source = DocumentHistorySource(path, revisions=3)
    html = client.get(path + '$history', HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(content=html, status_code=200)
    storage = mock_storage(spec=[
        'get_document_history', 'save_document_history'])
    resources = source.gather(requester, storage)
    history_path = path + '$history?limit=3'
    requester.request.assert_called_once_with(history_path,
                                              raise_for_status=False)
    rev1, rev2 = root_doc.revisions.all()
    revision_pattern = path + '$revision/%d'
    expected_resources = [
        ('revision', revision_pattern % rev.id, {}) for rev in [rev1, rev2]]
    assert resources == expected_resources
    assert source.state == source.STATE_DONE
    expected_data = {
        'is_all': True,
        'revisions': expected_resources[::-1]}
    storage.save_document_history.assert_called_once_with(
        'en-US', 'Root', expected_data)


def test_gather_error():
    """If the $history endpoint errors, scraping stops."""
    source = DocumentHistorySource('/en-US/docs/Error')
    requester = mock_requester(content="missing", status_code=404)
    storage = mock_storage(spec=[
        'get_document_history', 'save_document_history'])
    resources = source.gather(requester, storage)
    assert resources == []
    assert source.state == source.STATE_ERROR
    assert not storage.save_document_history.called


def test_gather_rev_existing():
    """If previously called, populate history from storage."""
    source = DocumentHistorySource('/en-US/docs/Root')
    storage = mock_storage(spec=['get_document_history'])
    storage.get_document_history.return_value = {
        'is_all': False,
        'revisions': [
            ('revision', '/en-US/docs/Root$revision/%d' % num, {})
            for num in range(10, 1, -1)]}
    resources = source.gather(None, storage)
    assert resources == [('revision', '/en-US/docs/Root$revision/10', {})]
    assert source.state == source.STATE_DONE


def test_gather_translated(translated_doc, client):
    """A translated document may include the English source doc."""
    path = translated_doc.get_absolute_url()
    source = DocumentHistorySource(path)
    html = client.get(path + '$history', HTTP_HOST=settings.WIKI_HOST).content
    requester = mock_requester(content=html, status_code=200)
    storage = mock_storage(spec=[
        'get_document_history', 'save_document_history'])
    resources = source.gather(requester, storage)
    history_path = path + '$history'
    requester.request.assert_called_once_with(history_path,
                                              raise_for_status=False)
    rev = translated_doc.current_revision
    rev_path = rev.get_absolute_url()
    based_on_path = rev.based_on.get_absolute_url()
    expected_resources = [('revision', rev_path, {'based_on': based_on_path})]
    assert resources == expected_resources
    assert source.state == source.STATE_DONE
    expected_data = {
        'is_all': False,
        'revisions': expected_resources}
    storage.save_document_history.assert_called_once_with(
        'fr', 'Racine', expected_data)
