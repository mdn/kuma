#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase
import pyes.exceptions

class ErrorReportingTestCase(ESTestCase):
    def setUp(self):
        super(ErrorReportingTestCase, self).setUp()
        self.conn.delete_index_if_exists("test-index")

    def tearDown(self):
        self.conn.delete_index_if_exists("test-index")

    def testCreateDelete(self):
        """Test errors thrown when creating or deleting indexes.

        """
        result = self.conn.create_index("test-index")
        self.assertTrue('ok' in result)
        self.assertTrue('error' not in result)

        err = self.checkRaises(pyes.exceptions.IndexAlreadyExistsException,
                               self.conn.create_index, "test-index")
        self.assertEqual(str(err), "[test-index] Already exists")
        self.assertEqual(err.status, 400)
        self.assertTrue('error' in err.result)
        self.assertTrue('ok' not in err.result)

        result = self.conn.delete_index("test-index")
        self.assertTrue('ok' in result)
        self.assertTrue('error' not in result)

        err = self.checkRaises(pyes.exceptions.IndexMissingException,
                               self.conn.delete_index, "test-index")
        self.assertEqual(str(err), "[test-index] missing")
        self.assertEqual(err.status, 404)
        self.assertTrue('error' in err.result)
        self.assertTrue('ok' not in err.result)

    def testMissingIndex(self):
        """Test generation of a IndexMissingException.

        """
        err = self.checkRaises(pyes.exceptions.IndexMissingException,
                               self.conn.flush, 'test-index')
        self.assertEqual(str(err), "[test-index] missing")
        self.assertEqual(err.status, 404)
        self.assertTrue('error' in err.result)
        self.assertTrue('ok' not in err.result)

    def testBadRequest(self):
        """Test error reported by doing a bad request.

        """
        err = self.checkRaises(pyes.exceptions.ElasticSearchException,
                               self.conn._send_request, 'GET', '_bad_request')
        self.assertEqual(str(err), "No handler found for uri [/_bad_request] and method [GET]")
        self.assertEqual(err.status, 400)
        self.assertEqual(err.result, 'No handler found for uri [/_bad_request] and method [GET]')

    def testDelete(self):
        """Test error reported by deleting a missing document.

        """
        self.checkRaises(pyes.exceptions.NotFoundException,
                               self.conn.delete, "test-index", "flibble",
                               "asdf")


if __name__ == "__main__":
    unittest.main()
