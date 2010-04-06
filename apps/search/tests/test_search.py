"""
Tests for the search (sphinx) app.
"""
import os
import shutil
import time

from django.test import client

from nose import SkipTest
import test_utils
import json

from manage import settings
from sumo.urlresolvers import reverse
from search.utils import start_sphinx, stop_sphinx, reindex
from search.clients import WikiClient


class SphinxTestCase(test_utils.TransactionTestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """

    fixtures = ['forums.json', 'threads.json', 'pages.json', 'categories.json']
    sphinx = True
    sphinx_is_running = False

    def setUp(self):
        if not SphinxTestCase.sphinx_is_running:
            if not settings.SPHINX_SEARCHD or not settings.SPHINX_INDEXER:
                raise SkipTest()

            os.environ['DJANGO_ENVIRONMENT'] = 'test'

            if os.path.exists('/tmp/data'):
                shutil.rmtree('/tmp/data')
            if os.path.exists('/tmp/log'):
                shutil.rmtree('/tmp/log')
            if os.path.exists('/tmp/etc'):
                shutil.rmtree('/tmp/etc')

            os.makedirs('/tmp/data')
            os.makedirs('/tmp/log')
            os.makedirs('/tmp/etc')
            reindex()
            start_sphinx()
            time.sleep(1)
            SphinxTestCase.sphinx_is_running = True

    @classmethod
    def tearDownClass(cls):
        if SphinxTestCase.sphinx_is_running:
            stop_sphinx()
            SphinxTestCase.sphinx_is_running = False


class SearchTest(SphinxTestCase):

    def test_indexer(self):
        wc = WikiClient()
        results = wc.query('practice')
        self.assertNotEquals(0, len(results))

    def test_category_filter(self):
        wc = WikiClient()
        results = wc.query('', ({'filter': 'category', 'value': [13]},))
        self.assertNotEquals(0, len(results))

    def test_category_exclude(self):
        c = client.Client()
        response = c.get(reverse('search'),
                         {'q': 'audio', 'format': 'json', 'w': 3})
        self.assertNotEquals(0, json.loads(response.content)['total'])

        response = c.get(reverse('search'),
                         {'q': 'audio', 'category': -13,
                          'format': 'json', 'w': 1})
        self.assertEquals(0, json.loads(response.content)['total'])
