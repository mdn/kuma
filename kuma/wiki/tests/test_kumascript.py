# -*- coding: utf-8 -*-
import json
import base64

import mock
from nose.tools import eq_, ok_

from kuma.wiki import kumascript
from . import WikiTestCase, document


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

    def test_url_normalization(self):
        """Ensure that template URLs are normalized to lowercase for kumascript"""
        eq_(kumascript._format_slug_for_request('Template:SomEthing'), 'Template:something')
        eq_(kumascript._format_slug_for_request('Template:SomEthing:Template:More'),
            'Template:something:template:more')

    @mock.patch('kuma.wiki.kumascript._format_slug_for_request')
    def test_get_calls_format_slug_for_templates(self, mock_format_slug):
        doc = document(title='Template:Test',
                       slug='Template:Test',
                       html='<%= "Test" %>',
                       save=True)
        mock_format_slug.return_value = doc.slug
        kumascript.get(doc, 'no-cache', 'https://testserver')
        ok_(mock_format_slug.called, "format slug should have been called")

    @mock.patch('kuma.wiki.kumascript._format_slug_for_request')
    def test_get_does_not_call_format_slug_for_docs(self, mock_format_slug):
        doc = document(title='Test',
                       slug='Test',
                       html='Test',
                       save=True)
        mock_format_slug.return_value = doc.slug
        kumascript.get(doc, 'no-cache', 'https://testserver')
        ok_(not mock_format_slug.called,
            "format slug should not have been called")
