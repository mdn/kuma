#!/usr/bin/env python
import zlib # implied prerequisite
import zipfile, os, StringIO, tempfile
from test.test_support import TestFailed
from py import test
from translate.misc import zipfileext

BrokenStringIO = StringIO.StringIO
class FixedStringIO(BrokenStringIO):
    def truncate(self, size=None):
        BrokenStringIO.truncate(self, size)
        self.len = len(self.buf)

StringIO.StringIO = FixedStringIO

# these tests won't all pass on zipfile module in Python 2.4
# there are extensions in zipfileext to add the delete method etc
# to test the underlying zipfile module, uncomment the following line:
zipfile.ZipFile = zipfileext.ZipFileExt

class TestZipFiles:
    def setup_method(self, method):
        self.srcname = "%s-%s%stmp" % (self.__class__.__name__, method.__name__, os.extsep)
        self.zipname = "%s-%s%szip" % (self.__class__.__name__, method.__name__, os.extsep)

    def teardown_method(self, method):
        # Remove temporary files
        if os.path.isfile(self.srcname):
            os.unlink(self.srcname)
        if os.path.isfile(self.zipname):
            os.unlink(self.zipname)

    def zipTest(self, f, compression, srccontents):
        zip = zipfile.ZipFile(f, "w", compression)   # Create the ZIP archive
        zip.write(self.srcname, "another"+os.extsep+"name")
        zip.write(self.srcname, self.srcname)
        zip.close()
    
        zip = zipfile.ZipFile(f, "r", compression)   # Read the ZIP archive
        readData2 = zip.read(self.srcname)
        readData1 = zip.read("another"+os.extsep+"name")
        zip.close()
    
        if readData1 != srccontents or readData2 != srccontents:
            raise TestFailed("Written data doesn't equal read data.")

    def deleteTest(self, f, compression, srccontents):
        zip = zipfile.ZipFile(f, "w", compression)   # Create the ZIP archive
        othername = "another"+os.extsep+"name"
        finalname = "adifferent"+os.extsep+"name"
        leftname, deletenames = othername, [self.srcname, finalname]
        zip.write(self.srcname, self.srcname)
        zip.write(self.srcname, othername)
        zip.write(self.srcname, finalname)
        zip.close()
    
        zip = zipfile.ZipFile(f, "a", compression)   # Modify the ZIP archive
        try:
            for deletename in deletenames:
                zip.delete(deletename)
        finally:
            zip.close()
    
        zip = zipfile.ZipFile(f, "r", compression)   # Read the ZIP archive
        try:
            testfailed = zip.testzip()
            readData = zip.read(leftname)
        finally:
            zip.close()
    
        assert not testfailed
        assert readData == srccontents

    def test_create_zip(self):
        fp = open(self.srcname, "wb")               # Make a source file with some lines
        for i in range(0, 1000):
            fp.write("Test of zipfile line %d.\n" % i)
        fp.close()
        
        fp = open(self.srcname, "rb")
        writtenData = fp.read()
        fp.close()
        
        for file in (self.zipname, tempfile.TemporaryFile(), StringIO.StringIO()):
            self.zipTest(file, zipfile.ZIP_STORED, writtenData)
        
        for file in (self.zipname, tempfile.TemporaryFile(), StringIO.StringIO()):
            self.zipTest(file, zipfile.ZIP_DEFLATED, writtenData)

    def test_delete_member(self):
        fp = open(self.srcname, "wb")               # Make a source file with some lines
        for i in range(0, 1000):
            fp.write("Test of zipfile line %d.\n" % i)
        fp.close()
        
        fp = open(self.srcname, "rb")
        writtenData = fp.read()
        fp.close()
        
        self.deleteTest(self.zipname, zipfile.ZIP_STORED, writtenData)
        self.deleteTest(tempfile.TemporaryFile(), zipfile.ZIP_STORED, writtenData)
        self.deleteTest(StringIO.StringIO(), zipfile.ZIP_STORED, writtenData)
        
        self.deleteTest(self.zipname, zipfile.ZIP_DEFLATED, writtenData)
        self.deleteTest(tempfile.TemporaryFile(), zipfile.ZIP_DEFLATED, writtenData)
        self.deleteTest(StringIO.StringIO(), zipfile.ZIP_DEFLATED, writtenData)

    def test_handles_error(self):
        """This test checks that the ZipFile constructor closes the file object"""
        """it opens if there's an error in the file.  If it doesn't, the traceback"""
        """holds a reference to the ZipFile object and, indirectly, the file object."""
        """On Windows, this causes the os.unlink() call to fail because the"""
        """underlying file is still open.  This is SF bug #412214."""
        fp = open(self.srcname, "w")
        fp.write("this is not a legal zip file\n")
        fp.close()
        assert test.raises(zipfile.BadZipfile, zipfile.ZipFile, self.srcname)
        os.unlink(self.srcname)

    def test_finalize(self):
        """make sure we don't raise an AttributeError when a partially-constructed"""
        """ZipFile instance is finalized; this tests for regression on SF tracker"""
        """bug #403871."""
        assert test.raises(IOError, zipfile.ZipFile, self.srcname)
        # The bug we're testing for caused an AttributeError to be raised
        # when a ZipFile instance was created for a file that did not
        # exist; the .fp member was not initialized but was needed by the
        # __del__() method.  Since the AttributeError is in the __del__(),
        # it is ignored, but the user should be sufficiently annoyed by
        # the message on the output that regression will be noticed
        # quickly.

    def test_fail_read_closed(self):
        # Verify that testzip() doesn't swallow inappropriate exceptions.
        data = StringIO.StringIO()
        zipf = zipfile.ZipFile(data, mode="w")
        zipf.writestr("foo.txt", "O, for a Muse of Fire!")
        zipf.close()
        zipf = zipfile.ZipFile(data, mode="r")
        zipf.close()
        # This is correct; calling .read on a closed ZipFile should throw
        # a RuntimeError, and so should calling .testzip.  An earlier
        # version of .testzip would swallow this exception (and any other)
        # and report that the first file in the archive was corrupt.
        assert test.raises(RuntimeError, zipf.testzip)
        del data, zipf

