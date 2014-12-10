#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import factory
from translate.storage.directory import Directory
from translate.misc import wStringIO

from gzip import GzipFile
try:
    # bz2 is not available on python 2.3
    from bz2 import BZ2File
except ImportError:
    BZ2File = None
import os

def classname(filename):
    """returns the classname to ease testing"""
    classinstance = factory.getclass(filename)
    return str(classinstance.__name__).lower()

def givefile(filename, content):
    """returns a file dummy object with the given content"""
    file = wStringIO.StringIO(content)
    file.name = filename
    return file

class BaseTestFactory:
    def setup_method(self, method):
        """sets up a test directory"""
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
    cleardir = classmethod(cleardir)

    def test_getclass(self):
        assert classname("file.po") == "pofile"
        assert classname("file.pot") == "pofile"
        assert classname("file.dtd.po") == "pofile"

        assert classname("file.tmx") == "tmxfile"
        assert classname("file.af.tmx") == "tmxfile"
        assert classname("file.tbx") == "tbxfile"
        assert classname("file.po.xliff") == "xlifffile"

        assert not classname("file.po") == "tmxfile"
        assert not classname("file.po") == "xlifffile"

        assert classname("file.po.gz") == "pofile"
        assert classname("file.pot.gz") == "pofile"
        assert classname("file.dtd.po.gz") == "pofile"

        assert classname("file.tmx.gz") == "tmxfile"
        assert classname("file.af.tmx.gz") == "tmxfile"
        assert classname("file.tbx.gz") == "tbxfile"
        assert classname("file.po.xliff.gz") == "xlifffile"

        assert not classname("file.po.gz") == "tmxfile"
        assert not classname("file.po.gz") == "xlifffile"

        assert classname("file.po.bz2") == "pofile"
        assert classname("file.pot.bz2") == "pofile"
        assert classname("file.dtd.po.bz2") == "pofile"

        assert classname("file.tmx.bz2") == "tmxfile"
        assert classname("file.af.tmx.bz2") == "tmxfile"
        assert classname("file.tbx.bz2") == "tbxfile"
        assert classname("file.po.xliff.bz2") == "xlifffile"

        assert not classname("file.po.bz2") == "tmxfile"
        assert not classname("file.po.bz2") == "xlifffile"

    def test_getobject(self):
        """Tests that we get a valid object."""
        fileobj = givefile(self.filename, self.file_content)
        store = factory.getobject(fileobj)
        assert isinstance(store, self.expected_instance)

    def test_get_noname_object(self):
        """Tests that we get a valid object from a file object without a name."""
        fileobj = wStringIO.StringIO(self.file_content)
        assert not hasattr(fileobj, 'name')
        store = factory.getobject(fileobj)
        assert isinstance(store, self.expected_instance)

    def test_gzfile(self):
        """Test that we can open a gzip file correctly."""
        filename = os.path.join(self.testdir, self.filename + '.gz')
        gzfile = GzipFile(filename, mode="wb")
        gzfile.write(self.file_content)
        gzfile.close()
        store = factory.getobject(filename)
        assert isinstance(store, self.expected_instance)

    def test_bz2file(self):
        """Test that we can open a gzip file correctly."""
        if not BZ2File:
            return
        filename = os.path.join(self.testdir, self.filename + '.bz2')
        bz2file = BZ2File(filename, mode="wb")
        bz2file.write(self.file_content)
        bz2file.close()
        store = factory.getobject(filename)
        assert isinstance(store, self.expected_instance)

    def test_directory(self):
        """Test that a directory is correctly detected."""
        object = factory.getobject(self.testdir)
        assert isinstance(object, Directory)

class TestPOFactory(BaseTestFactory):
    expected_instance = factory.po.pofile
    filename = 'dummy.po'
    file_content = '''#: test.c\nmsgid "test"\nmsgstr "rest"\n'''

class TestXliffFactory(BaseTestFactory):
    expected_instance = factory.xliff.xlifffile
    filename = 'dummy.xliff'
    file_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
<file>
<body>
  <trans-unit>
    <source>test</source>
    <target>rest</target>
  </trans-unit>
</body>
</file>
</xliff>'''

class TestPOXliffFactory(BaseTestFactory):
    expected_instance = factory.poxliff.PoXliffFile
    filename = 'dummy.xliff'
    file_content = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
<file datatype="po" original="file.po" source-language="en-US"><body><trans-unit approved="no" id="1" restype="x-gettext-domain-header" xml:space="preserve">
<source>MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
</source>
<target>MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
</target>
</trans-unit></body></file></xliff>'''

class TestWordfastFactory(BaseTestFactory):
    expected_instance = factory.wordfast.WordfastTMFile
    filename = 'dummy.txt'
    file_content = '''%20070801~103212	%User ID,S,S SMURRAY,SMS Samuel Murray-Smit,SM Samuel Murray-Smit,MW Mary White,DS Deepak Shota,MT! Machine translation (15),AL! Alignment (10),SM Samuel Murray,	%TU=00000075	%AF-ZA	%Wordfast TM v.5.51r/00	%EN-ZA	%---80597535	Subject (5),EL,EL Electronics,AC Accounting,LE Legal,ME Mechanics,MD Medical,LT Literary,AG Agriculture,CO Commercial	Client (5),LS,LS LionSoft Corp,ST SuperTron Inc,CA CompArt Ltd			
20070801~103248	SM	0	AF-ZA	Langeraad en duimpie	EN-ZA	Big Ben and Little John	EL	LS'''
