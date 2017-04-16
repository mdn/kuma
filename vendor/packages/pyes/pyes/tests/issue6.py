#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Issue #6 testcase.
"""
import unittest
from pyes.tests import ESTestCase
from pyes import MatchAllQuery

class QuerySearchTestCase(ESTestCase):
    def test_ReconvertDoubles(self):
        """Regression test for issue#6.

        Pyes used to fail when getting a query respones in which a document
        contained a list of doubles.

        """
        q = MatchAllQuery()
        result = self.conn.search(query=q, indexes=["test-pindex"])
        self.assertEquals(result['hits']['total'], 2)

if __name__ == "__main__":
    unittest.main()
