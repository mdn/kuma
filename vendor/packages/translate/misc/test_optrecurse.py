#!/usr/bin/env python

import os

from translate.misc import optrecurse


class TestRecursiveOptionParser:

    def test_splitext(self):
        """test the ``optrecurse.splitext`` function"""
        self.parser = optrecurse.RecursiveOptionParser({"txt": ("po", None)})
        name = "name"
        extension = "ext"
        filename = name + os.extsep + extension
        dirname = os.path.join("some", "path", "to")
        fullpath = os.path.join(dirname, filename)
        root = os.path.join(dirname, name)
        print(fullpath)
        assert self.parser.splitext(fullpath) == (root, extension)
