#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin and the lang-javascript plugin running on the default port (localhost:9500).
"""
from pyestest import ESTestCase
from pyes.facets import DateHistogramFacet
from pyes.filters import TermFilter, RangeFilter
from pyes.query import FilteredQuery, MatchAllQuery
from pyes.utils import ESRange
import unittest

import datetime

class FacetSearchTestCase(ESTestCase):
    def setUp(self):
        super(FacetSearchTestCase, self).setUp()
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
                 u'position': {'store': 'yes',
                               'type': u'integer'},
                 u'tag': {'store': 'yes',
                          'type': u'string'},
                 u'date': {'store': 'yes',
                           'type': u'date'},
                 u'uuid': {'boost': 1.0,
                           'index': 'not_analyzed',
                           'store': 'yes',
                           'type': u'string'}}
        self.conn.create_index("test-index")
        self.conn.put_mapping("test-type", {'properties':mapping}, ["test-index"])
        self.conn.index({"name": "Joe Tester",
                         "parsedtext": "Joe Testere nice guy",
                         "uuid": "11111",
                         "position": 1,
                         "tag": "foo",
                         "date": datetime.date(2011, 5, 16)}, "test-index", "test-type", 1)
        self.conn.index({"name":" Bill Baloney",
                         "parsedtext": "Bill Testere nice guy",
                         "uuid": "22222",
                         "position": 2,
                         "tag": "foo",
                         "date": datetime.date(2011, 4, 16)}, "test-index", "test-type", 2)
        self.conn.index({"name": "Bill Clinton",
                         "parsedtext": "Bill is not nice guy",
                         "uuid": "33333",
                         "position": 3,
                         "tag": "bar",
                         "date": datetime.date(2011, 4, 28)}, "test-index", "test-type", 3)
        self.conn.refresh(["test-index"])

    def test_terms_facet(self):
        q = MatchAllQuery()
        q = q.search()
        q.facet.add_term_facet('tag')
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 3)
        self.assertEquals(result['facets']['tag']['terms'], [{u'count': 2, u'term': u'foo'},
                                                             {u'count': 1, u'term': u'bar'}])

    def test_terms_facet_filter(self):
        q = MatchAllQuery()
        q = FilteredQuery(q, TermFilter('tag', 'foo'))
        q = q.search()
        q.facet.add_term_facet('tag')
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 2)
        self.assertEquals(result['facets']['tag']['terms'], [{u'count': 2, u'term': u'foo'}])

    def test_date_facet(self):
        q = MatchAllQuery()
        q = q.search()
        q.facet.facets.append(DateHistogramFacet('date_facet',
                                                 field='date',
                                                 interval='month'))
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 3)
        self.assertEquals(result['facets']['date_facet']['entries'], [{u'count': 2, u'time': 1301616000000},
                                                                      {u'count': 1, u'time': 1304208000000}])
        self.assertEquals(datetime.datetime.fromtimestamp(1301616000000/1000.).date(),
                          datetime.date(2011, 04, 01))
        self.assertEquals(datetime.datetime.fromtimestamp(1304208000000/1000.).date(),
                          datetime.date(2011, 05, 01))

    def test_date_facet_filter(self):
        q = MatchAllQuery()
        q = FilteredQuery(q, RangeFilter(qrange=ESRange('date',
                                                        datetime.date(2011, 4, 1),
                                                        datetime.date(2011, 5, 1),
                                                        include_upper=False)))
        q = q.search()
        q.facet.facets.append(DateHistogramFacet('date_facet',
                                                 field='date',
                                                 interval='month'))
        result = self.conn.search(query=q, indexes=["test-index"], doc_types=["test-type"])
        self.assertEquals(result['hits']['total'], 2)
        self.assertEquals(result['facets']['date_facet']['entries'], [{u'count': 2, u'time': 1301616000000}])

if __name__ == "__main__":
    unittest.main()
