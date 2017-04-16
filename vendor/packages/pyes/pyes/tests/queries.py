#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin and the lang-javascript plugin running on the default port (localhost:9500).
"""
from pyestest import ESTestCase
from pyes.query import *
from pyes.filters import TermFilter, ANDFilter, ORFilter
import unittest

class QuerySearchTestCase(ESTestCase):
    def setUp(self):
        super(QuerySearchTestCase, self).setUp()
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
        self.conn.put_mapping("test-type2", {"_parent" : {"type" : "test-type"}}, ["test-index"])
        self.conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "uuid":"11111", "position":1}, "test-index", "test-type", 1)
        self.conn.index({"name":"data1", "value":"value1"}, "test-index", "test-type2", 1, parent=1)
        self.conn.index({"name":"Bill Baloney", "parsedtext":"Bill Testere nice guy", "uuid":"22222", "position":2}, "test-index", "test-type", 2)
        self.conn.index({"name":"data2", "value":"value2"}, "test-index", "test-type2", 2, parent=2)
        self.conn.index({"name":"Bill Clinton", "parsedtext":"""Bill is not 
                nice guy""", "uuid":"33333", "position":3}, "test-index", "test-type", 3)
        self.conn.refresh(["test-index"])

    def test_TermQuery(self):
        q = TermQuery("name", "joe")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q = TermQuery("name", "joe", 3)
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q = TermQuery("name", "joe", "3")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_WildcardQuery(self):
        q = WildcardQuery("name", "jo*")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q = WildcardQuery("name", "jo*", 3)
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q = WildcardQuery("name", "jo*", "3")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_PrefixQuery(self):
        q = PrefixQuery("name", "jo")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q = PrefixQuery("name", "jo", 3)
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q = PrefixQuery("name", "jo", "3")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_MatchAllQuery(self):
        q = MatchAllQuery()
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 3)

    def test_StringQuery(self):
        q = StringQuery("joe AND test")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 0)

        q = StringQuery("joe OR test")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

        q1 = StringQuery("joe")
        q2 = StringQuery("test")
        q = BoolQuery(must=[q1, q2])
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 0)

        q = BoolQuery(should=[q1, q2])
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_OR_AND_Filters(self):
        q1 = TermFilter("position", 1)
        q2 = TermFilter("position", 2)
        andq = ANDFilter([q1, q2])

        q = FilteredQuery(MatchAllQuery(), andq)
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 0)

        orq = ORFilter([q1, q2])
        q = FilteredQuery(MatchAllQuery(), orq)
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 2)

    def test_FieldQuery(self):
        q = FieldQuery(FieldParameter("name", "+joe"))
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_DisMaxQuery(self):
        q = DisMaxQuery(FieldQuery(FieldParameter("name", "+joe")))
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_HasChildQuery(self):
        q = HasChildQuery(type="test-type2", query=TermQuery("name", "data1"))
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_RegexTermQuery(self):
        # Don't run this test, because it depends on the RegexTermQuery
        # feature which is not currently in elasticsearch trunk.
        return

        q = RegexTermQuery("name", "jo.")
        result = self.conn.search(query=q, indexes=["test-index"])
        self.assertEquals(result['hits']['total'], 1)

    def test_CustomScoreQueryMvel(self):
        q = CustomScoreQuery(query=MatchAllQuery(),
                             lang="mvel",
                             script="_score*(5+doc.position.value)"
                             )
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 3)
        self.assertEquals(result['hits']['hits'][0]['_score'], 8.0)
        self.assertEquals(result['hits']['hits'][1]['_score'], 7.0)
        self.assertEquals(result['hits']['max_score'], 8.0)

    def test_CustomScoreQueryJS(self):
        q = CustomScoreQuery(query=MatchAllQuery(),
                             lang="js",
                             script="parseFloat(_score*(5+doc.position.value))"
                             )
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 3)
        self.assertEquals(result['hits']['hits'][0]['_score'], 8.0)
        self.assertEquals(result['hits']['hits'][1]['_score'], 7.0)
        self.assertEquals(result['hits']['max_score'], 8.0)

    def test_CustomScoreQueryPython(self):
        q = CustomScoreQuery(query=MatchAllQuery(),
                             lang="python",
                             script="parseFloat(_score*(5+doc.position.value))"
                             )
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 3)
        self.assertEquals(result['hits']['hits'][0]['_score'], 8.0)
        self.assertEquals(result['hits']['hits'][1]['_score'], 7.0)
        self.assertEquals(result['hits']['max_score'], 8.0)

if __name__ == "__main__":
    unittest.main()
