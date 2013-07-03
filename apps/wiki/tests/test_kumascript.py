# This Python file uses the following encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# see also: http://www.python.org/dev/peps/pep-0263/
import datetime
import logging
import json
import base64
import hashlib
import time

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import Q

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from . import TestCaseBase
from wiki import kumascript

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
            for k,v in headers.items()
            if k.startswith(pfx))

        # Ensure the env vars intended for kumascript match expected values.
        for n in ('title', 'slug', 'locale', 'path'):
            eq_(env_vars[n], result_vars[n])
        eq_(sorted([u'foo', u'bar', u'baz']), sorted(result_vars['tags']))
