#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyestest import ESTestCase
from pyes.rivers import CouchDBRiver, RabbitMQRiver, TwitterRiver

class RiversTestCase(ESTestCase):
    def setUp(self):
        super(RiversTestCase, self).setUp()

    def testCreateCouchDBRiver(self):
        """
        Testing deleting a river
        """
        test_river = CouchDBRiver(index_name='text_index', index_type='test_type')
        result = self.conn.create_river(test_river, river_name='test_index')
        print result
        self.assertResultContains(result, {'ok': True})

    def testDeleteCouchDBRiver(self):
        """
        Testing deleting a river
        """
        test_river = CouchDBRiver(index_name='text_index', index_type='test_type')
        result = self.conn.delete_river(test_river, river_name='test_index')
        print result
        self.assertResultContains(result, {'ok': True})

    def testCreateRabbitMQRiver(self):
        """
        Testing deleting a river
        """
        test_river = RabbitMQRiver(index_name='text_index', index_type='test_type')
        result = self.conn.create_river(test_river, river_name='test_index')
        print result
        self.assertResultContains(result, {'ok': True})

    def testDeleteRabbitMQRiver(self):
        """
        Testing deleting a river
        """
        test_river = RabbitMQRiver(index_name='text_index', index_type='test_type')
        result = self.conn.delete_river(test_river, river_name='test_index')
        print result
        self.assertResultContains(result, {'ok': True})

    def testCreateTwitterRiver(self):
        """
        Testing deleting a river
        """
        test_river = TwitterRiver('test', 'test', index_name='text_index', index_type='test_type')
        result = self.conn.create_river(test_river, river_name='test_index')
        print result
        self.assertResultContains(result, {'ok': True})

    def testDeleteTwitterRiver(self):
        """
        Testing deleting a river
        """
        test_river = TwitterRiver('test', 'test', index_name='text_index', index_type='test_type')
        result = self.conn.delete_river(test_river, river_name='test_index')
        print result
        self.assertResultContains(result, {'ok': True})

if __name__ == "__main__":
    unittest.main()

