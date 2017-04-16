#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase
from pyes import *
from time import sleep

class ESRelatedTestCase(ESTestCase):
    def setUp(self):
        super(ESRelatedTestCase, self).setUp()
        self.conn.create_index("test-index")
        self.conn.refresh(["test-index"])

    def test_IDSaving(self):
        url = "http://tests.com/mytest/?related=ok" 
        self.conn.index({"name":"Joe Tester", "parsedtext":"Joe Testere nice guy", "url":url, "uuid":"11111", "position":1}, "test-index", "test-type", string_b64encode(url))
        self.conn.refresh(["test-index"])
        res = self.conn.get("test-index", "test-type", string_b64encode(url))
        self.assertEquals(res['_source']['url'], url)

if __name__ == "__main__":
    unittest.main()