# -*- coding: utf-8 -*-
import json

import mock
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


@mock.patch('json.dumps')
def test_server_side_render(mock_dumps, mock_requests, settings):
    """For server-side rendering expect a div with some content and
       a script with less data than we'd get for client-side rendering
    """
    mock_dumps.side_effect = sorted_json_dumps

    # This is the input to the mock Node server
    body = 'article content'
    toc = 'table of contents'
    links = 'sidebar'
    contributors = ['a', 'b']
    data = {
        'bodyHTML': body,
        'tocHTML': toc,
        'quickLinksHTML': links,
        'contributors': contributors
    }

    # This will be the output sent by the mock Node server
    mock_html = '<p>{}</p><p>{}</p><p>{}</p><p>{}</p>'.format(
        body, toc, links, contributors)

    mock_requests.post(settings.SSR_URL, text=mock_html)

    # Run the template tag
    output = ssr.render_react_app(data)

    # Make sure the output is as expected
    # The HTML attributes in the data should not be repeated in the output
    data.update(bodyHTML='', tocHTML='', quickLinksHTML='')
    assert output == (
        u'<div id="react-container">{}</div>\n'
        u'<script>window._document_data = {};</script>\n'
    ).format(mock_html, json.dumps(data))


@mock.patch('json.dumps')
def test_client_side_render(mock_dumps):
    """For client-side rendering expect a script json data and an empty div."""
    mock_dumps.side_effect = sorted_json_dumps
    data = {'x': 'one', 'y': 2, 'z': ['a', 'b']}
    output = ssr.render_react_app(data, ssr=False)
    assert output == (
        u'<div id="react-container"></div>\n'
        u'<script>window._document_data = {};</script>\n'
    ).format(json.dumps(data))


@pytest.mark.parametrize('failure_class', [
    requests.exceptions.ConnectionError,
    requests.exceptions.ReadTimeout])
@mock.patch('json.dumps')
def test_failed_server_side_render(mock_dumps, failure_class,
                                   mock_requests, settings):
    """If SSR fails, we should do client-side rendering instead."""
    mock_dumps.side_effect = sorted_json_dumps
    mock_requests.post(settings.SSR_URL, exc=failure_class('message'))
    data = {'x': 'one', 'y': 2, 'z': ['a', 'b']}
    assert ssr.render_react_app(data) == ssr.render_react_app(data, ssr=False)
