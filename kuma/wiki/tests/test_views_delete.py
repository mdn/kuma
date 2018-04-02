import pytest
from django.contrib.auth.models import Permission

from kuma.core.urlresolvers import reverse

from ..models import Document, DocumentDeletionLog


@pytest.fixture
def delete_client(editor_client, wiki_user):
    wiki_user.user_permissions.add(
        Permission.objects.get(codename='purge_document'),
        Permission.objects.get(codename='delete_document'),
        Permission.objects.get(codename='restore_document')
    )
    return editor_client


@pytest.mark.parametrize('endpoint', ['revert_document', 'delete_document',
                                      'restore_document', 'purge_document'])
def test_login(root_doc, client, endpoint):
    """Tests that login is required. The "client" fixture is not logged in."""
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), locale='en-US', args=args)
    response = client.get(url)
    assert response.status_code == 302
    assert 'en-US/users/signin?' in response['Location']
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


@pytest.mark.parametrize(
    'endpoint', ['delete_document', 'restore_document', 'purge_document'])
def test_permission(root_doc, editor_client, endpoint):
    """
    Tests that the proper permission is required. The "editor_client"
    fixture, although logged in, does not have the proper permission.
    """
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), locale='en-US', args=args)
    response = editor_client.get(url)
    assert response.status_code == 403
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


@pytest.mark.parametrize('endpoint', ['revert_document', 'delete_document',
                                      'restore_document', 'purge_document'])
def test_read_only_mode(root_doc, user_client, endpoint):
    args = [root_doc.slug]
    if endpoint == 'revert_document':
        args.append(root_doc.current_revision.id)
    url = reverse('wiki.{}'.format(endpoint), locale='en-US', args=args)
    response = user_client.get(url)
    assert response.status_code == 403
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


def test_delete_get(root_doc, delete_client):
    url = reverse('wiki.delete_document', locale='en-US', args=[root_doc.slug])
    response = delete_client.get(url)
    assert response.status_code == 200
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


@pytest.mark.xfail(reason='The "wiki/confirm_purge.html" template is missing'
                          ' (see bugzilla 1197390).')
def test_purge_get(root_doc, delete_client):
    root_doc.delete()
    url = reverse('wiki.purge_document', locale='en-US', args=[root_doc.slug])
    response = delete_client.get(url)
    assert response.status_code == 200
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


def test_restore_get(root_doc, delete_client):
    root_doc.delete()
    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)
    url = reverse('wiki.restore_document', locale='en-US',
                  args=[root_doc.slug])
    response = delete_client.get(url)
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    assert Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)


def test_revert_get(root_doc, delete_client):
    url = reverse('wiki.revert_document', locale='en-US',
                  args=[root_doc.slug, root_doc.current_revision.id])
    response = delete_client.get(url)
    assert response.status_code == 200
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']


def test_delete_post(root_doc, delete_client):
    url = reverse('wiki.delete_document', locale='en-US', args=[root_doc.slug])
    response = delete_client.post(url, data=dict(reason='test'))
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    assert len(Document.admin_objects.filter(
        slug=root_doc.slug, locale=root_doc.locale, deleted=True)) == 1
    with pytest.raises(Document.DoesNotExist):
        Document.objects.get(slug=root_doc.slug, locale=root_doc.locale)
    assert len(DocumentDeletionLog.objects.filter(locale=root_doc.locale,
                                                  slug=root_doc.slug,
                                                  reason='test')) == 1


def test_purge_post(root_doc, delete_client):
    root_doc.delete()
    url = reverse('wiki.purge_document', locale='en-US', args=[root_doc.slug])
    response = delete_client.post(url, data=dict(confirm='true'))
    assert response.status_code == 302
    assert response['Location'].endswith(root_doc.get_absolute_url())
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    with pytest.raises(Document.DoesNotExist):
        Document.admin_objects.get(slug=root_doc.slug, locale=root_doc.locale)


def test_revert_post(edit_revision, delete_client):
    root_doc = edit_revision.document
    assert len(root_doc.revisions.all()) == 2
    first_revision = root_doc.revisions.first()
    url = reverse('wiki.revert_document', locale='en-US',
                  args=[root_doc.slug, first_revision.id])
    response = delete_client.post(url, data=dict(comment='test'))
    assert response.status_code == 302
    assert response['Location'].endswith(reverse('wiki.document_revisions',
                                                 args=[root_doc.slug]))
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    assert len(root_doc.revisions.all()) == 3
    root_doc.refresh_from_db()
    assert root_doc.current_revision.id != edit_revision.id
    assert root_doc.current_revision.id != first_revision.id
    assert root_doc.current_revision.id == root_doc.revisions.last().id
