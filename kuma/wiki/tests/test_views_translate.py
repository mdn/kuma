from django.contrib.auth.models import Permission
from pyquery import PyQuery as pq
import pytest

from kuma.core.urlresolvers import reverse
from kuma.wiki.models import Document


@pytest.fixture
def permission_change_document(db):
    return Permission.objects.get(codename='change_document')


@pytest.fixture
def trans_doc_client(editor_client, wiki_user, permission_change_document):
    wiki_user.user_permissions.add(permission_change_document)
    return editor_client


def test_translate_get(root_doc, trans_doc_client):
    """Test GET on the translate view."""

    url = reverse(
        'wiki.translate', args=(root_doc.slug,), locale=root_doc.locale)
    url += '?tolocale=fr'

    response = trans_doc_client.get(url)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    page = pq(response.content)
    assert page.find('input[name=slug]')[0].value == root_doc.slug


def test_translate_post(root_doc, trans_doc_client):
    """Test POST on the translate view."""

    data = {
        'slug': root_doc.slug,
        'title': root_doc.title,
        'content': root_doc.current_revision.content,
        'form-type': 'both',
        'toc_depth': 1
    }

    url = reverse(
        'wiki.translate', args=(root_doc.slug,), locale=root_doc.locale)
    url += '?tolocale=fr'

    response = trans_doc_client.post(url, data)
    assert response.status_code == 302
    assert response['X-Robots-Tag'] == 'noindex'
    assert 'max-age=0' in response['Cache-Control']
    assert 'no-cache' in response['Cache-Control']
    assert 'no-store' in response['Cache-Control']
    assert 'must-revalidate' in response['Cache-Control']
    doc_url = reverse('wiki.document', args=(root_doc.slug,), locale='fr')
    assert doc_url + '?rev_saved=' in response['Location']
    assert len(Document.objects.filter(locale='fr', slug=root_doc.slug)) == 1
    # Ensure there is no redirect.
    assert len(Document.objects.filter(
        title=root_doc.title + ' Redirect 1', locale='fr')) == 0
