from datetime import datetime

import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse

from ..models import Document, Revision


@pytest.fixture
def purge_client(admin_client):
    yield admin_client


@pytest.fixture
def another_root_doc(wiki_user):
    """Another newly-created top-level English document."""
    root_doc = Document.objects.create(
        locale="en-US", slug="AnotherRoot", title="Another Root Document"
    )
    Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content="<p>Getting started again...</p>",
        title="Another Root Document",
        created=datetime(2017, 5, 14, 12, 15),
    )
    return root_doc


def test_login(client):
    """Tests that login is required. The "client" fixture is not logged in."""
    url = reverse("wiki.admin_bulk_purge")
    response = client.get(url)
    assert response.status_code == 302
    assert "en-US/users/signin?" in response["Location"]
    assert_no_cache_header(response)


def test_staff_permission(editor_client):
    """
    Tests that staff permission is required. The "editor_client"
    fixture, although logged in, does not have staff permission.
    """
    url = reverse("wiki.admin_bulk_purge")
    response = editor_client.get(url)
    assert response.status_code == 302
    assert response["Location"].endswith(
        "admin/login/?next=/admin/wiki/document/purge/"
    )
    assert_no_cache_header(response)


def test_purge_get(root_doc, another_root_doc, purge_client):
    root_doc.delete()
    another_root_doc.delete()
    url = reverse("wiki.admin_bulk_purge")
    response = purge_client.get(
        url, {"ids": "{},{}".format(root_doc.id, another_root_doc.id)}
    )
    assert response.status_code == 200
    assert_no_cache_header(response)
    # Make sure nothing has happended (i.e. the docs haven't been purged).
    for doc in (root_doc, another_root_doc):
        assert Document.admin_objects.get(slug=doc.slug, locale=doc.locale)


def test_purge_post(root_doc, another_root_doc, purge_client):
    root_doc.delete()
    another_root_doc.delete()
    query_params = "?ids={},{}".format(root_doc.id, another_root_doc.id)
    url = reverse("wiki.admin_bulk_purge") + query_params
    response = purge_client.post(url, data={"confirm_purge": "true"})
    assert response.status_code == 302
    assert response["Location"].endswith("/admin/wiki/document/")
    assert_no_cache_header(response)
    for doc in (root_doc, another_root_doc):
        with pytest.raises(Document.DoesNotExist):
            Document.admin_objects.get(slug=doc.slug, locale=doc.locale)
