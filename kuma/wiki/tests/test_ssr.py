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


@pytest.mark.parametrize('locale', ['en-US', 'es'])
@mock.patch('json.dumps')
@mock.patch('kuma.wiki.templatetags.ssr.get_localization_data')
def test_server_side_render(mock_get_l10n_data, mock_dumps, locale,
                            mock_requests, settings):
    """For server-side rendering expect a div with some content and
       a script with less data than we'd get for client-side rendering
    """

    mock_dumps.side_effect = sorted_json_dumps

    # This is the input to the mock Node server
    body = 'article content'
    toc = 'table of contents'
    links = 'sidebar'
    contributors = ['a', 'b']
    document_data = {
        'bodyHTML': body,
        'tocHTML': toc,
        'quickLinksHTML': links,
        'contributors': contributors
    }
    request_data = {
        'locale': locale
    }

    localization_data = {'catalog': {'s': locale}}
    mock_get_l10n_data.side_effect = lambda l: localization_data

    data = {
        'localizationData': localization_data,
        'documentData': document_data,
        'requestData': request_data
    }

    # This will be the output sent by the mock Node server
    mock_html = '<p>{}</p><p>{}</p><p>{}</p><p>{}</p>'.format(
        body, toc, links, contributors)

    mock_requests.post(settings.SSR_URL, text=mock_html)

    # Run the template tag
    output = ssr.render_react_app(locale, document_data, request_data)

    # Make sure the output is as expected
    # The HTML attributes in the data should not be repeated in the output
    document_data.update(bodyHTML='', tocHTML='', quickLinksHTML='')
    assert output == (
        u'<div id="react-container">{}</div>\n'
        u'<script>window._react_data = {};</script>\n'
    ).format(mock_html, json.dumps(data))


@mock.patch('json.dumps')
@mock.patch('kuma.wiki.templatetags.ssr.get_localization_data')
def test_client_side_render(mock_get_l10n_data, mock_dumps):
    """For client-side rendering expect a script json data and an empty div."""
    localization_data = {'catalog': {'s': 't'}}
    mock_get_l10n_data.side_effect = lambda l: localization_data

    mock_dumps.side_effect = sorted_json_dumps
    document_data = {'x': 'one', 'y': 2, 'z': ['a', 'b']}
    request_data = {
        'locale': 'en-US'
    }
    data = {
        'localizationData': localization_data,
        'documentData': document_data,
        'requestData': request_data
    }
    output = ssr.render_react_app('en-US', document_data, request_data,
                                  ssr=False)
    assert output == (
        u'<div id="react-container"></div>\n'
        u'<script>window._react_data = {};</script>\n'
    ).format(json.dumps(data))


@pytest.mark.parametrize('failure_class', [
    requests.exceptions.ConnectionError,
    requests.exceptions.ReadTimeout])
@mock.patch('json.dumps')
@mock.patch('kuma.wiki.templatetags.ssr.get_localization_data')
def test_failed_server_side_render(mock_get_l10n_data,
                                   mock_dumps, failure_class,
                                   mock_requests, settings):
    """If SSR fails, we should do client-side rendering instead."""
    localization_data = {'catalog': {'s': 't'}}
    mock_get_l10n_data.side_effect = lambda l: localization_data
    mock_dumps.side_effect = sorted_json_dumps
    mock_requests.post(settings.SSR_URL, exc=failure_class('message'))
    document_data = {'x': 'one', 'y': 2, 'z': ['a', 'b']}
    request_data = {
        'locale': 'en-US'
    }
    assert (ssr.render_react_app('en-US', document_data, request_data) ==
            ssr.render_react_app('en-US', document_data, request_data,
                                 ssr=False))
