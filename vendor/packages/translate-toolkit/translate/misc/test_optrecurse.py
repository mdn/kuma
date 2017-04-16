#!/usr/bin/env python

from translate.misc import optrecurse
import os

class TestRecursiveOptionParser:

    def __init__(self):
        self.parser = optrecurse.RecursiveOptionParser({"txt":("po", None)})

    def test_splitext(self):
        """test the L{optrecurse.splitext} function"""
        name = "name"
        extension = "ext"
        filename = name + os.extsep + extension
        dirname = os.path.join("some", "path", "to")
        fullpath = os.path.join(dirname, filename)
        root = os.path.join(dirname, name)
        print fullpath
        assert self.parser.splitext(fullpath) == (root, extension)
