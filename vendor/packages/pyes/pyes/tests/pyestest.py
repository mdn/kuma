#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""

import unittest
from pyes import ES
from pprint import pprint

def get_conn(*args, **kwargs):
    return ES('127.0.0.1:9200', *args, **kwargs)

class ESTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = get_conn()
        self.conn.delete_index_if_exists("test-index")

    def tearDown(self):
        self.conn.delete_index_if_exists("test-index")

    def assertResultContains(self, result, expected):
        for (key, value) in expected.items():
            self.assertEquals(value, result[key])

    def checkRaises(self, excClass, callableObj, *args, **kwargs):
        """Assert that calling callableObj with *args and **kwargs raises an
        exception of type excClass, and return the exception object so that
        further tests on it can be performed.
        """
        try:
            callableObj(*args, **kwargs)
        except excClass, e:
            return e
        else:
            raise self.failureException, \
                "Expected exception %s not raised" % excClass

    def dump(self, result):
        """
        dump to stdout the result
        """
        pprint(result)

main = unittest.main
