import pytest

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.parametrize("method", ["get", "head"])
def test_revision_hash(client, db, method, settings):
    settings.REVISION_HASH = "the_revision_hash"
    response = getattr(client, method)(reverse("version.kuma"))
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert_no_cache_header(response)
    if method == "get":
        assert response.content.decode() == "the_revision_hash"


@pytest.mark.parametrize("method", ["post", "put", "delete", "options", "patch"])
def test_revision_hash_405s(client, db, method):
    response = getattr(client, method)(reverse("version.kuma"))
    assert response.status_code == 405
    assert_no_cache_header(response)
