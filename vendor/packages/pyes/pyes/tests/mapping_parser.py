#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for pyes.  These require an es server with thrift plugin running on the default port (localhost:9500).
"""
import unittest
from pyes.tests import ESTestCase
from pyes import decode_json
from pyes.mappings import Mapper
import os

class MapperTestCase(ESTestCase):
    def setUp(self):
        super(MapperTestCase, self).setUp()
        self.datamap = decode_json(open(os.path.join("data", "map.json"), "rb").read())

    def test_parser(self):
        _ = Mapper(self.datamap)

        mapping = self.conn.get_mapping()
        self.dump(mapping)


if __name__ == "__main__":
    unittest.main()
