#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase

class ClusterTestCase(ESTestCase):
    def setUp(self):
        super(ClusterTestCase, self).setUp()
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
        self.conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "uuid":"11111", "position":1}, "test-index", "test-type", 1)
        self.conn.index({"name":"Bill Baloney", "parsedtext":"Bill Testere nice guy", "uuid":"22222", "position":2}, "test-index", "test-type", 2)
        self.conn.index({"name":"Bill Clinton", "parsedtext":"""Bill is not 
                nice guy""", "uuid":"33333", "position":3}, "test-index", "test-type", 3)
        self.conn.refresh(["test-index"])

    def test_ClusterState(self):
        result = self.conn.cluster_state()
        self.assertTrue('blocks' in result)
        self.assertTrue('routing_table' in result)

    def test_ClusterNodes(self):
        result = self.conn.cluster_nodes()
        self.assertTrue('cluster_name' in result)
        self.assertTrue('nodes' in result)

    def test_ClusterHealth(self):
        result = self.conn.cluster_health()
        print "health"
        print result

if __name__ == "__main__":
    unittest.main()
