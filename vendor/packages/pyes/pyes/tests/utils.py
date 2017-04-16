#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'

"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase
from pyes import TermQuery, clean_string, ResultSet
from datetime import datetime

class SerializationTestCase(ESTestCase):
    def setUp(self):
        super(SerializationTestCase, self).setUp()
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
                 u'inserted': {'store': 'yes',
                            'type': u'date'},
                 u'uuid': {'boost': 1.0,
                           'index': 'not_analyzed',
                           'store': 'yes',
                           'type': u'string'}}
        self.conn.create_index("test-index")
        self.conn.put_mapping("test-type", {'properties':mapping}, ["test-index"])
        self.conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "uuid":"11111", "position":1, 'inserted':datetime(2010, 10, 22, 12, 12, 12)}, "test-index", "test-type", 1)
        self.conn.index({"name":"Bill Baloney", "parsedtext":"Joe Testere nice guy", "uuid":"22222", "position":2, 'inserted':datetime(2010, 10, 22, 12, 12, 10)}, "test-index", "test-type", 2)
        self.conn.refresh(["test-index"])

    def test_TermQuery(self):
        q = TermQuery("parsedtext", "joe")
        result = self.conn.search(query=q, indexes="test-index")
        self.dump(result)
        result = ResultSet(result)
        self.assertEquals(result.total, 2)
        self.assertEquals(result.max_score, 0.15342641000000001)

#        self.assertEquals(result['hits']['hits'][0]['_source']['inserted'], datetime(2010, 10, 22, 12, 12, 12))

    def test_cleanstring(self):
        self.assertEquals(clean_string("senthil("), "senthil")
        self.assertEquals(clean_string("senthil&"), "senthil")
        self.assertEquals(clean_string("senthil-"), "senthil")
        self.assertEquals(clean_string("senthil:"), "senthil")

if __name__ == "__main__":
    unittest.main()
