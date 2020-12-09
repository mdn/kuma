import json
from unittest import mock

import pytest
import requests.exceptions

from kuma.wiki.templatetags import ssr


# To compare JSON strings (rather than object equality) we really need
# to ensure that the properties of a dict are in a deteriministic order.
# so we're going to patch json.dumps to call this function that sorts
# the dict keys alphabetically.
def sorted_json_dumps(o):
    return real_json_dumps(o, sort_keys=True)


real_json_dumps = json.dumps


@pytest.mark.parametrize("locale", ["en-US", "es"])
@mock.patch("json.dumps")
@mock.patch("kuma.wiki.templatetags.ssr.get_localization_data")
def test_server_side_render(
    mock_get_l10n_data, mock_dumps, locale, mock_requests, settings
):
    """For server-side rendering expect a div with some content and
    a script with less data than we'd get for client-side rendering
    """

    mock_dumps.side_effect = sorted_json_dumps

    # This is the input to the mock Node server
    body = "article content"
    toc = "table of contents"
    links = "sidebar"
    contributors = ["a", "b"]
    document_data = {
        "bodyHTML": body,
        "tocHTML": toc,
        "quickLinksHTML": links,
        "contributors": contributors,
    }

    localization_data = {"catalog": {"s": locale}, "plural": None}
    mock_get_l10n_data.side_effect = lambda l: localization_data

    # This will be the output sent by the mock Node server
    mock_html = "<p>{}</p><p>{}</p><p>{}</p><p>{}</p>".format(
        body, toc, links, contributors
    )

    url = "{}/{}".format(settings.SSR_URL, "SPA")

    mock_requests.post(url, json={"html": mock_html, "script": "STUFF"})

    # Run the template tag
    path = "/en-US/docs/foo"
    output = ssr.render_react("SPA", locale, path, document_data)

    # Make sure the output is as expected
    expect = (
        f'<div id="react-container" data-component-name="SPA">{mock_html}</div>\n'
        "<script>window._react_data = JSON.parse(STUFF);</script>\n"
    )
    assert output == expect


@mock.patch("json.dumps")
@mock.patch("kuma.wiki.templatetags.ssr.get_localization_data")
def test_client_side_render(mock_get_l10n_data, mock_dumps):
    """For client-side rendering expect a script json data and an empty div."""
    localization_data = {"catalog": {"s": "t"}, "plural": None}
    mock_get_l10n_data.side_effect = lambda l: localization_data

    mock_dumps.side_effect = sorted_json_dumps
    document_data = {"x": "one", "y": 2, "z": ["a", "b"]}
    path = "/en-US/docs/foo"
    data = {
        "locale": "en-US",
        "url": path,
        "stringCatalog": localization_data["catalog"],
        "documentData": document_data,
        "pluralExpression": None,
    }
    output = ssr.render_react("page", "en-US", path, document_data, ssr=False)
    expected = (
        '<div id="react-container" data-component-name="{}"></div>\n'
        "<script>window._react_data = {};</script>\n"
    ).format("page", json.dumps(data))
    assert output == expected


@pytest.mark.parametrize(
    "failure_class",
    [
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout,
        requests.exceptions.HTTPError,
    ],
)
@mock.patch("json.dumps")
@mock.patch("kuma.wiki.templatetags.ssr.get_localization_data")
def test_failed_server_side_render(
    mock_get_l10n_data, mock_dumps, failure_class, mock_requests, settings
):
    """If SSR fails, we should do client-side rendering instead."""
    localization_data = {"catalog": {"s": "t"}, "plural": None}
    mock_get_l10n_data.side_effect = lambda l: localization_data
    mock_dumps.side_effect = sorted_json_dumps
    url = f"{settings.SSR_URL}/page"
    mock_requests.post(url, exc=failure_class("message"))
    document_data = {"x": "one", "y": 2, "z": ["a", "b"]}
    path = "/en-US/docs/foo"
    assert ssr.render_react("page", "en-US", path, document_data) == ssr.render_react(
        "page", "en-US", path, document_data, ssr=False
    )
