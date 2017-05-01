# -*- coding: utf-8 -*-
import base64
import json
from urlparse import urljoin

import mock
import pytest
import requests_mock
from elasticsearch import TransportError
from elasticsearch_dsl.connections import connections

from kuma.core.tests import eq_
from kuma.wiki import kumascript
from kuma.wiki.constants import KUMASCRIPT_BASE_URL
from . import WikiTestCase


@pytest.yield_fixture
def mock_es_client(request):
    """
    Mock ElasticSearch client.

    User should override client.search.return_value.
    Based on test fixture from elasticsearch_dsl
    """
    client = mock.Mock()
    connections.add_connection('default', client)
    yield client
    connections._conn = {}
    connections._kwargs = {}


class KumascriptClientTests(WikiTestCase):

    def test_env_vars(self):
        """Exercise building of env var headers for kumascript"""
        headers = dict()
        env_vars = dict(
            path='/foo/test-slug',
            title='Test title',
            slug='test-slug',
            locale='de',
            tags=[u'foo', u'bar', u'baz']
        )
        kumascript.add_env_headers(headers, env_vars)

        pfx = 'x-kumascript-env-'
        result_vars = dict(
            (k[len(pfx):], json.loads(base64.b64decode(v)))
            for k, v in headers.items()
            if k.startswith(pfx))

        # Ensure the env vars intended for kumascript match expected values.
        for n in ('title', 'slug', 'locale', 'path'):
            eq_(env_vars[n], result_vars[n])
        eq_(sorted([u'foo', u'bar', u'baz']), sorted(result_vars['tags']))


@requests_mock.mock()
def test_macro_sources(mock_requests):
    """When KumaScript returns macros, the sources are populated."""
    macros_url = urljoin(KUMASCRIPT_BASE_URL, 'macros/')
    response = {
        'can_list_macros': True,
        'loader': 'FileLoader',
        'macros': [{
            'filename': 'A11yRoleQuicklinks.ejs', 'name': 'A11yRoleQuicklinks'
        }, {
            'filename': 'APIFeatureList.ejs', 'name': 'APIFeatureList'
        }, {
            # Normal form D, common on OSX
            'filename': u'traduccio\u0301n.ejs', 'name': u'traduccio\u0301n'
        }]
    }
    mock_requests.get(macros_url, json=response)
    macros = kumascript.macro_sources()
    expected = {
        'A11yRoleQuicklinks': 'A11yRoleQuicklinks.ejs',
        'APIFeatureList': 'APIFeatureList.ejs',
        # Normal form C, used on GitHub, ElasticSearch
        u'traducci\xf3n': u'traducci\xf3n.ejs',
    }
    assert macros == expected


@requests_mock.mock()
def test_macro_sources_empty_macro_list(mock_requests):
    """When KumaScript can't return macros, the sources are empty."""
    macros_url = urljoin(KUMASCRIPT_BASE_URL, 'macros/')
    response = {
        'can_list_macros': False,
        'loader': 'HTTPLoader',
        'macros': []
    }
    mock_requests.get(macros_url, json=response)
    macros = kumascript.macro_sources()
    assert macros == {}


@requests_mock.mock()
def test_macro_sources_error(mock_requests):
    """When KumaScript raises an error, the sources are empty."""
    macros_url = urljoin(KUMASCRIPT_BASE_URL, 'macros/')
    mock_requests.get(macros_url, status_code=404, text='Cannot GET /macros')
    macros = kumascript.macro_sources()
    assert macros == {}


def test_macro_page_count(mock_es_client):
    """macro_page_count returns macro usage across all locales by default."""
    mock_es_client.search.return_value = {
        '_shards': {u'failed': 0, u'successful': 2, u'total': 2},
        'aggregations': {'usage': {'buckets': [
            {'key': 'a11yrolequicklinks', 'doc_count': 200},
            {'key': 'othermacro', 'doc_count': 50},
        ]}},
        'hits': {'hits': [], 'max_score': 0.0, 'total': 45556},
        'timed_out': False,
        'took': 18
    }

    macros = kumascript.macro_page_count()

    es_json = {
        'size': 0,
        'query': {'match_all': {}},
        'aggs': {'usage': {'terms': {
            'field': 'kumascript_macros',
            'size': 0}
        }}
    }
    mock_es_client.search.assert_called_once_with(body=es_json, doc_type=[],
                                                  index=None)
    assert macros == {'a11yrolequicklinks': 200, 'othermacro': 50}


def test_macro_page_count_en(mock_es_client):
    """macro_page_count('en-US') returns macro usage in the en-US locale."""
    mock_es_client.search.return_value = {
        '_shards': {u'failed': 0, u'successful': 2, u'total': 2},
        'aggregations': {'usage': {'buckets': [
            {'key': 'a11yrolequicklinks', 'doc_count': 100},
            {'key': 'othermacro', 'doc_count': 30},
        ]}},
        'hits': {'hits': [], 'max_score': 0.0, 'total': 45556},
        'timed_out': False,
        'took': 18
    }

    macros = kumascript.macro_page_count(locale='en-US')

    es_json = {
        'size': 0,
        'query': {'filtered': {
            'filter': {'term': {'locale': 'en-US'}},
            'query': {'match_all': {}}
        }},
        'aggs': {'usage': {'terms': {
            'field': 'kumascript_macros',
            'size': 0}
        }},
    }
    mock_es_client.search.assert_called_once_with(body=es_json, doc_type=[],
                                                  index=None)
    assert macros == {'a11yrolequicklinks': 100, 'othermacro': 30}


@mock.patch('kuma.wiki.kumascript.macro_page_count')
@mock.patch('kuma.wiki.kumascript.macro_sources')
def test_macro_usage(mock_sources, mock_page_count):
    mock_sources.return_value = {
        'A11yRoleQuicklinks': 'A11yRoleQuicklinks.ejs',
        'APIFeatureList': 'APIFeatureList.ejs',
    }
    all_page_count = {'a11yrolequicklinks': 200, 'othermacro': 50}
    en_page_count = {'a11yrolequicklinks': 101, 'othermacro': 42}
    mock_page_count.side_effect = [all_page_count, en_page_count]

    usage = kumascript.macro_usage()

    expected = {
        'A11yRoleQuicklinks': {
            'github_subpath': 'A11yRoleQuicklinks.ejs',
            'count': 200,
            'en_count': 101,
        },
        'APIFeatureList': {
            'github_subpath': 'APIFeatureList.ejs',
            'count': 0,
            'en_count': 0
        }
    }
    assert usage == expected


@mock.patch('kuma.wiki.kumascript.macro_page_count')
@mock.patch('kuma.wiki.kumascript.macro_sources')
def test_macro_usage_empty_kumascript(mock_sources, mock_page_count):
    """When KumaScript returns an empty response, macro usage is empty."""
    mock_sources.return_value = {}
    mock_page_count.side_effect = Exception('should not be called')
    macros = kumascript.macro_usage()
    assert macros == {}


@mock.patch('kuma.wiki.kumascript.macro_page_count')
@mock.patch('kuma.wiki.kumascript.macro_sources')
def test_macro_usage_elasticsearch_exception(mock_sources, mock_page_count):
    """When ElasticSearch is unreachable, counts are 0."""
    mock_sources.return_value = {
        'A11yRoleQuicklinks': 'A11yRoleQuicklinks.ejs'
    }
    mock_page_count.side_effect = TransportError("Can't reach ElasticSearch")

    macros = kumascript.macro_usage()

    expected = {
        'A11yRoleQuicklinks': {
            'github_subpath': 'A11yRoleQuicklinks.ejs',
            'count': 0,
            'en_count': 0,
        }
    }
    assert macros == expected


@mock.patch('kuma.wiki.kumascript.macro_page_count')
@mock.patch('kuma.wiki.kumascript.macro_sources')
def test_macro_usage_2nd_es_exception(mock_sources, mock_page_count):
    """When follow-on ElasticSearch call raises, reraise exception."""
    mock_sources.return_value = {
        'A11yRoleQuicklinks': 'A11yRoleQuicklinks.ejs'
    }
    mock_page_count.side_effect = [
        {'a11yrolequicklinks': 200, 'othermacro': 50},
        TransportError("Can't reach ElasticSearch")
    ]

    with pytest.raises(TransportError):
        kumascript.macro_usage()
