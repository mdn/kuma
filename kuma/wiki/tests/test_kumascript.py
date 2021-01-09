import base64
import json
from unittest import mock
from urllib.parse import urljoin

import pytest
import requests_mock
from elasticsearch_dsl.connections import connections
from requests.exceptions import (
    ConnectionError,
    ContentDecodingError,
    ReadTimeout,
    TooManyRedirects,
)

from . import WikiTestCase
from .. import kumascript
from ..constants import KUMASCRIPT_BASE_URL


@pytest.fixture
def mock_es_client(request):
    """
    Mock ElasticSearch client.

    User should override client.search.return_value.
    """
    client = mock.Mock()
    connections._conns["default"] = client
    yield client
    del connections._conns["default"]


class KumascriptClientTests(WikiTestCase):
    def test_env_vars(self):
        """Exercise building of env var headers for kumascript"""
        headers = dict()
        env_vars = dict(
            path="/foo/test-slug",
            title="Test title",
            slug="test-slug",
            locale="de",
            tags=["foo", "bar", "baz"],
        )
        kumascript.add_env_headers(headers, env_vars)

        pfx = "x-kumascript-env-"
        result_vars = dict(
            (k[len(pfx) :], json.loads(base64.b64decode(v)))
            for k, v in headers.items()
            if k.startswith(pfx)
        )

        # Ensure the env vars intended for kumascript match expected values.
        for n in ("title", "slug", "locale", "path"):
            assert env_vars[n] == result_vars[n]
        assert {"foo", "bar", "baz"} == set(result_vars["tags"])


def test_macro_sources(mock_requests):
    """When KumaScript returns macros, the sources are populated."""
    macros_url = urljoin(KUMASCRIPT_BASE_URL, "macros/")
    response = {
        "can_list_macros": True,
        "loader": "FileLoader",
        "macros": [
            {"filename": "A11yRoleQuicklinks.ejs", "name": "A11yRoleQuicklinks"},
            {"filename": "APIFeatureList.ejs", "name": "APIFeatureList"},
            {
                # Normal form D, common on OSX
                "filename": "traduccio\u0301n.ejs",
                "name": "traduccio\u0301n",
            },
        ],
    }
    mock_requests.get(macros_url, json=response)
    macros = kumascript.macro_sources()
    expected = {
        "A11yRoleQuicklinks": "A11yRoleQuicklinks.ejs",
        "APIFeatureList": "APIFeatureList.ejs",
        # Normal form C, used on GitHub, ElasticSearch
        "traducci\xf3n": "traducci\xf3n.ejs",
    }
    assert macros == expected


def test_macro_sources_empty_macro_list(mock_requests):
    """When KumaScript can't return macros, the sources are empty."""
    macros_url = urljoin(KUMASCRIPT_BASE_URL, "macros/")
    response = {"can_list_macros": False, "loader": "HTTPLoader", "macros": []}
    mock_requests.get(macros_url, json=response)
    macros = kumascript.macro_sources()
    assert macros == {}


def test_macro_sources_error(mock_requests):
    """When KumaScript raises an error, the sources are empty."""
    macros_url = urljoin(KUMASCRIPT_BASE_URL, "macros/")
    mock_requests.get(macros_url, status_code=404, text="Cannot GET /macros")
    macros = kumascript.macro_sources()
    assert macros == {}


@pytest.mark.parametrize("exc_cls", [ConnectionError, ReadTimeout])
def test_get_with_requests_exception(root_doc, mock_requests, exc_cls):
    """Test that connection and timeout errors are handled for get."""
    mock_requests.post(requests_mock.ANY, exc=exc_cls("some I/O error"))
    body, errors = kumascript.get(root_doc, "https://example.com", timeout=1)
    assert body == root_doc.html
    assert errors == [
        {"level": "error", "message": "some I/O error", "args": [exc_cls.__name__]}
    ]


@pytest.mark.parametrize("exc_cls", [ContentDecodingError, TooManyRedirects])
def test_get_with_other_exception(root_doc, mock_requests, exc_cls):
    """Test that non-connection/non-timeout errors are not handled for get."""
    mock_requests.post(requests_mock.ANY, exc=exc_cls("requires attention"))
    with pytest.raises(exc_cls):
        kumascript.get(root_doc, "https://example.com", timeout=1)


@pytest.mark.parametrize("exc_cls", [ConnectionError, ReadTimeout])
def test_post_with_requests_exception(db, rf, mock_requests, exc_cls):
    """Test that connection and timeout errors are handled for post."""
    content = "some freshly edited content"
    request = rf.get("/en-US/docs/preview-wiki-content")
    mock_requests.post(requests_mock.ANY, exc=exc_cls("some I/O error"))
    body, errors = kumascript.post(request, content)
    assert body == content
    assert errors == [
        {"level": "error", "message": "some I/O error", "args": [exc_cls.__name__]}
    ]


@pytest.mark.parametrize("exc_cls", [ContentDecodingError, TooManyRedirects])
def test_post_with_other_exception(db, rf, mock_requests, exc_cls):
    """Test that non-connection/non-timeout errors are not handled for post."""
    content = "some freshly edited content"
    request = rf.get("/en-US/docs/preview-wiki-content")
    mock_requests.post(requests_mock.ANY, exc=exc_cls("requires attention"))
    with pytest.raises(exc_cls):
        kumascript.post(request, content)
