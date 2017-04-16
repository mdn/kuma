#!/usr/bin/env python

"""Tests for the zip storage module"""

from translate.storage import directory
from translate.storage import zip
import os
from zipfile import ZipFile

class TestZIPFile(object):
    """A test class to test the zip class that provides the directory interface."""

    def setup_method(self, method):
        """sets up a test directory"""
        print "setup_method called on", self.__class__.__name__
        self.testzip = "%s_testzip.zip" % (self.__class__.__name__)
        self.cleardir(self.testzip)
        self.zip = ZipFile(self.testzip, mode="w")

    def teardown_method(self, method):
        """removes the attributes set up by setup_method"""
        self.cleardir(self.testzip)

    def cleardir(self, dirname):
        """removes the given directory"""
        if os.path.exists(self.testzip):
            os.remove(self.testzip)
        assert not os.path.exists(self.testzip)

    def touchfiles(self, dir, filenames, content="", last=False):
        for filename in filenames:
            if dir:
                self.zip.writestr(os.path.join(dir, filename), content)
            else:
                self.zip.writestr(filename, content)
        if last:
            self.zip.close()

    def mkdir(self, dir):
        """Makes a directory inside self.testzip."""
        pass

    def test_created(self):
        """test that the directory actually exists"""
        print self.testzip
        assert os.path.isfile(self.testzip)

    def test_basic(self):
        """Tests basic functionality."""
        files = ["a.po", "b.po", "c.po"]
        self.touchfiles(None, files, last=True)

        d = zip.ZIPFile(self.testzip)
        filenames = [name for dir, name in d.getfiles()]
        assert filenames == files

    def test_structure(self):
        """Tests a small directory structure."""
        files = ["a.po", "b.po", "c.po"]
        self.touchfiles(self.testzip, files)
        self.mkdir("bla")
        self.touchfiles(os.path.join(self.testzip, "bla"), files, last=True)
        
        d = zip.ZIPFile(self.testzip)
        filenames = [name for dir, name in d.getfiles()]
        assert filenames == files*2

    def test_getunits(self):
        """Tests basic functionality."""
        files = ["a.po", "b.po", "c.po"]
        posource = '''msgid "bla"\nmsgstr "blabla"\n'''
        self.touchfiles(self.testzip, files, posource, last=True)

        d = zip.ZIPFile(self.testzip)
        for unit in d.getunits():
            assert unit.target == "blabla"
        assert len(d.getunits()) == 3
