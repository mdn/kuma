# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import json
import base64

from nose.tools import eq_

from . import TestCaseBase
from kuma.wiki import kumascript


class KumascriptClientTests(TestCaseBase):

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
