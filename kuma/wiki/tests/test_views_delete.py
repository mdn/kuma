import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse

from ..models import Document, DocumentDeletionLog


@pytest.mark.parametrize('endpoint', ['revert_document', 'delete_document'])
def test_login(root_doc, client, endpoint):
    """Tests that login is required. The "client" fixture is not logged in."""
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), args=args)
    response = client.get(url)
    assert response.status_code == 302
    assert 'en-US/users/signin?' in response['Location']
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    'endpoint', ['delete_document'])
def test_permission(root_doc, editor_client, endpoint):
    """
    Tests that the proper permission is required. The "editor_client"
    fixture, although logged in, does not have the proper permission.
    """
    args = [root_doc.slug]
    url = reverse('wiki.{}'.format(endpoint), args=args)
    response = editor_client.get(url)
    assert response.status_code == 403
    assert_no_cache_header(response)


@pytest.mark.parametrize('endpoint', ['revert_document', 'delete_document'])
def test_read_only_mode(root_doc, user_client, endpoint):
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), args=args)
    response = user_client.get(url)
    assert response.status_code == 403
    assert_no_cache_header(response)


def test_delete_get(root_doc, moderator_client):
    url = reverse('wiki.delete_document', args=[root_doc.slug])
    response = moderator_client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)


def test_delete_post(root_doc, moderator_client):
    url = reverse('wiki.delete_document', args=[root_doc.slug])
    response = moderator_client.post(url, data=dict(reason='test'))
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert_no_cache_header(response)

    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)
    assert len(DocumentDeletionLog.objects.filter(locale=root_doc.locale,
                                                  slug=root_doc.slug,
                                                  reason='test')) == 1
