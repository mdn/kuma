#!/usr/bin/env python

"""Tests for the directory module"""

from translate.storage import directory
import os

class TestDirectory(object):
    """a test class to run tests on a test Pootle Server"""

    def setup_method(self, method):
        """sets up a test directory"""
        print "setup_method called on", self.__class__.__name__
        self.testdir = "%s_testdir" % (self.__class__.__name__)
        self.cleardir(self.testdir)
        os.mkdir(self.testdir)

    def teardown_method(self, method):
        """removes the attributes set up by setup_method"""
        self.cleardir(self.testdir)

    def cleardir(self, dirname):
        """removes the given directory"""
        if os.path.exists(dirname):
            for dirpath, subdirs, filenames in os.walk(dirname, topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in subdirs:
                    os.rmdir(os.path.join(dirpath, name))
        if os.path.exists(dirname): os.rmdir(dirname)
        assert not os.path.exists(dirname)

    def touchfiles(self, dir, filenames, content=None):
        for filename in filenames:
            f = open(os.path.join(dir, filename), "w")
            if content:
                f.write(content)
            f.close()

    def mkdir(self, dir):
        """Makes a directory inside self.testdir."""
        os.mkdir(os.path.join(self.testdir, dir))

    def test_created(self):
        """test that the directory actually exists"""
        print self.testdir
        assert os.path.isdir(self.testdir)

    def test_basic(self):
        """Tests basic functionality."""
        files = ["a.po", "b.po", "c.po"]
        files.sort()
        self.touchfiles(self.testdir, files)

        d = directory.Directory(self.testdir)
        filenames = [name for dir, name in d.getfiles()]
        filenames.sort()
        assert filenames == files

    def test_structure(self):
        """Tests a small directory structure."""
        files = ["a.po", "b.po", "c.po"]
        self.touchfiles(self.testdir, files)
        self.mkdir("bla")
        self.touchfiles(os.path.join(self.testdir, "bla"), files)
        
        d = directory.Directory(self.testdir)
        filenames = [name for dirname, name in d.getfiles()]
        filenames.sort()
        files = files*2
        files.sort()
        assert filenames == files

    def test_getunits(self):
        """Tests basic functionality."""
        files = ["a.po", "b.po", "c.po"]
        posource = '''msgid "bla"\nmsgstr "blabla"\n'''
        self.touchfiles(self.testdir, files, posource)

        d = directory.Directory(self.testdir)
        for unit in d.getunits():
            assert unit.target == "blabla"
        assert len(d.getunits()) == 3
