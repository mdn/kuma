#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin and the lang-javascript plugin running on the default port (localhost:9500).
"""
from pyestest import ESTestCase
from pyes.query import *
import unittest

class PercolatorTestCase(ESTestCase):
    def setUp(self):
        super(PercolatorTestCase, self).setUp()
        mapping = { u'parsedtext': {'boost': 1.0,
                         'index': 'analyzed',
                         'store': 'yes',
                         'type': u'string',
                         "term_vector" : "with_positions_offsets"},
                 u'name': {'boost': 1.0,
                            'index': 'analyzed',
                            'store': 'yes',
                            'type': u'string',
                            "term_vector" : "with_positions_offsets"},
                 u'title': {'boost': 1.0,
                            'index': 'analyzed',
                            'store': 'yes',
                            'type': u'string',
                            "term_vector" : "with_positions_offsets"},
                 u'pos': {'store': 'yes',
                            'type': u'integer'},
                 u'uuid': {'boost': 1.0,
                           'index': 'not_analyzed',
                           'store': 'yes',
                           'type': u'string'}}
        self.conn.create_index("test-index")
        self.conn.put_mapping("test-type", {'properties':mapping}, ["test-index"])
        self.conn.create_percolator(
            'test-index',
            'test-perc1',
            StringQuery(query='apple', search_fields='_all')
        )
        self.conn.create_percolator(
            'test-index',
            'test-perc2',
            StringQuery(query='apple OR iphone', search_fields='_all')
        )
        self.conn.create_percolator(
            'test-index',
            'test-perc3',
            StringQuery(query='apple AND iphone', search_fields='_all')
        )
        self.conn.refresh(["test-index"])

    def test_percolator(self):
        results = self.conn.percolate('test-index', 'test-type', PercolatorQuery({'name': 'iphone'}))
        self.assertTrue('test-perc1' not in results['matches'])
        self.assertTrue('test-perc2' in results['matches'])
        self.assertTrue('test-perc3' not in results['matches'])

    def test_or(self):
        results = self.conn.percolate('test-index', 'test-type', PercolatorQuery({'name': 'apple'}))
        self.assertTrue('test-perc1' in results['matches'])
        self.assertTrue('test-perc2' in results['matches'])
        self.assertTrue('test-perc3' not in results['matches'])

    def test_and(self):
        results = self.conn.percolate('test-index', 'test-type', PercolatorQuery({'name': 'apple iphone'}))
        self.assertTrue('test-perc1' in results['matches'])
        self.assertTrue('test-perc2' in results['matches'])
        self.assertTrue('test-perc3' in results['matches'])

    def tearDown(self):
        self.conn.delete_percolator('test-index', 'test-perc1')
        self.conn.delete_percolator('test-index', 'test-perc2')
        self.conn.delete_percolator('test-index', 'test-perc3')
        super(PercolatorTestCase, self).tearDown()


if __name__ == "__main__":
    unittest.main()
