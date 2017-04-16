#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase
from pyes import TermQuery

class BulkTestCase(ESTestCase):
    def setUp(self):
        super(BulkTestCase, self).setUp()
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
        self.conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "uuid":"11111", "position":1}, "test-index", "test-type", 1, bulk=True)
        self.conn.index({"name":"Bill Baloney", "parsedtext":"Bill Testere nice guy", "uuid":"22222", "position":2}, "test-index", "test-type", 2, bulk=True)
        self.conn.index({"name":"Bill Clinton", "parsedtext":"""Bill is not 
                nice guy""", "uuid":"33333", "position":3}, "test-index", "test-type", 3, bulk=True)
        self.conn.force_bulk()
        self.conn.refresh(["test-index"])

    def test_TermQuery(self):
        q = TermQuery("name", "bill")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 2)

if __name__ == "__main__":
    unittest.main()