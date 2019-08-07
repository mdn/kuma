from django.conf import settings
import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse

from ..models import Document, DocumentDeletionLog


@pytest.mark.parametrize('endpoint', ['revert_document', 'delete_document',
                                      'restore_document', 'purge_document'])
def test_login(root_doc, client, endpoint):
    """Tests that login is required. The "client" fixture is not logged in."""
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), args=args)
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert 'en-US/users/signin?' in response['Location']
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    'endpoint', ['delete_document', 'restore_document', 'purge_document'])
def test_permission(root_doc, editor_client, endpoint):
    """
    Tests that the proper permission is required. The "editor_client"
    fixture, although logged in, does not have the proper permission.
    """
    args = [root_doc.slug]
    url = reverse('wiki.{}'.format(endpoint), args=args)
    response = editor_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403
    assert_no_cache_header(response)


@pytest.mark.parametrize('endpoint', ['revert_document', 'delete_document',
                                      'restore_document', 'purge_document'])
def test_read_only_mode(root_doc, user_client, endpoint):
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), args=args)
    response = user_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403
    assert_no_cache_header(response)


def test_delete_get(root_doc, moderator_client):
    url = reverse('wiki.delete_document', args=[root_doc.slug])
    response = moderator_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert_no_cache_header(response)


def test_purge_get(deleted_doc, moderator_client):
    url = reverse('wiki.purge_document', args=[deleted_doc.slug])
    response = moderator_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert_no_cache_header(response)
    assert 'This document was deleted by' in response.content.decode('utf-8')


def test_purge_get_no_log(deleted_doc, moderator_client):
    url = reverse('wiki.purge_document', args=[deleted_doc.slug])
    DocumentDeletionLog.objects.all().delete()
    response = moderator_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert_no_cache_header(response)
    assert 'deleted, for unknown reasons' in response.content.decode('utf-8')


def test_restore_get(root_doc, moderator_client):
    root_doc.delete()
    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)
    url = reverse('wiki.restore_document', args=[root_doc.slug])
    response = moderator_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert_no_cache_header(response)
    assert Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)


def test_revert_get(root_doc, moderator_client):
    url = reverse('wiki.revert_document',
                  args=[root_doc.slug, root_doc.current_revision.id])
    response = moderator_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert_no_cache_header(response)


def test_delete_post(root_doc, moderator_client):
    url = reverse('wiki.delete_document', args=[root_doc.slug])
    response = moderator_client.post(url, data=dict(reason='test'),
                                     HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert_no_cache_header(response)
    assert len(Document.admin_objects.filter(
        slug=root_doc.slug, locale=root_doc.locale, deleted=True)) == 1
    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)
    assert len(DocumentDeletionLog.objects.filter(locale=root_doc.locale,
                                                  slug=root_doc.slug,
                                                  reason='test')) == 1


def test_purge_post(root_doc, moderator_client):
    root_doc.delete()
    url = reverse('wiki.purge_document', args=[root_doc.slug])
    response = moderator_client.post(url, data=dict(confirm='true'),
                                     HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert_no_cache_header(response)
    with pytest.raises(Document.DoesNotExist):
        Document.admin_objects.get(slug=root_doc.slug, locale=root_doc.locale)


def test_revert_post(edit_revision, moderator_client):
    root_doc = edit_revision.document
    assert len(root_doc.revisions.all()) == 2
    first_revision = root_doc.revisions.first()
    url = reverse('wiki.revert_document',
                  args=[root_doc.slug, first_revision.id])
    response = moderator_client.post(url, data=dict(comment='test'),
                                     HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert response['Location'].endswith(reverse('wiki.document_revisions',
                                                 args=[root_doc.slug]))
    assert_no_cache_header(response)
    assert len(root_doc.revisions.all()) == 3
    root_doc.refresh_from_db()
    assert root_doc.current_revision.id != edit_revision.id
    assert root_doc.current_revision.id != first_revision.id
    assert root_doc.current_revision.id == root_doc.revisions.last().id
