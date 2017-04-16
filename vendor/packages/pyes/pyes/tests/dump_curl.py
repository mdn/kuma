#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase, get_conn
import StringIO

class DumpCurlTestCase(ESTestCase):
    def setUp(self):
        super(DumpCurlTestCase, self).setUp()

    def testDumpCurl(self):
        """Test errors thrown when creating or deleting indexes.

        """
        dump = StringIO.StringIO()
        conn = get_conn(dump_curl=dump)
        result = conn.index(dict(title="Hi"), "test-index", "test-type")
        self.assertTrue('ok' in result)
        self.assertTrue('error' not in result)

        dump = dump.getvalue()
        self.assertTrue('test-index/test-type -d \"{\\"title\\": \\"Hi\\"}\"\n'
                        in dump)

if __name__ == "__main__":
    unittest.main()
