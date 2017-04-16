import zlib # implied prerequisite
import zipfile, os, StringIO, tempfile
try:
    from test.test_support import TestFailed
except ImportError:
    class TestFailed(Exception):
        pass
from translate.misc import zipfileext

BrokenStringIO = StringIO.StringIO
class FixedStringIO(BrokenStringIO):
    def truncate(self, size=None):
        BrokenStringIO.truncate(self, size)
        self.len = len(self.buf)

StringIO.StringIO = FixedStringIO

def zipTest(srcname, f, compression, srccontents):
    zip = zipfileext.ZipFileExt(f, "w", compression)   # Create the ZIP archive
    zip.write(srcname, "another"+os.extsep+"name")
    zip.write(srcname, srcname)
    zip.close()

    zip = zipfileext.ZipFileExt(f, "r", compression)   # Read the ZIP archive
    readData2 = zip.read(srcname)
    readData1 = zip.read("another"+os.extsep+"name")
    zip.close()

    if readData1 != srccontents or readData2 != srccontents:
        raise TestFailed, "Written data doesn't equal read data."

def deleteTest(srcname, f, compression, srccontents):
    zip = zipfileext.ZipFileExt(f, "w", compression)   # Create the ZIP archive
    othername = "another"+os.extsep+"name"
    finalname = "adifferent"+os.extsep+"name"
    leftname, deletenames = othername, [srcname, finalname]
    zip.write(srcname, srcname)
    zip.write(srcname, othername)
    zip.write(srcname, finalname)
    zip.close()

    zip = zipfileext.ZipFileExt(f, "a", compression)   # Modify the ZIP archive
    for deletename in deletenames:
        zip.delete(deletename)
    zip.close()

    zip = zipfileext.ZipFileExt(f, "r", compression)   # Read the ZIP archive
    testfailed = zip.testzip()
    readData = zip.read(leftname)
    zip.close()

    if testfailed:
        raise TestFailed, "zip file didn't pass test"
    if readData != srccontents:
        raise TestFailed, "Written data doesn't equal read data."

class TestZipfile:

    def setup_method(self, method):
        print repr(method), dir(method)
        self.srcname = self.__class__.__name__ + "_" + method.__name__ + os.extsep + "tmp"
        self.zipname = self.__class__.__name__ + "_" + method.__name__ + os.extsep + "zip"
        if os.path.exists(self.srcname):
            os.remove(self.srcname)
        if os.path.exists(self.zipname):
            os.remove(self.zipname)

    def teardown_method(self, method):
        if os.path.exists(self.srcname):           # Remove temporary files
            os.unlink(self.srcname)
        if os.path.exists(self.zipname):
            os.unlink(self.zipname)

    def test_consistent(self):
        fp = open(self.srcname, "wb")               # Make a source file with some lines
        for i in range(0, 1000):
            fp.write("Test of zipfile line %d.\n" % i)
        fp.close()
        
        fp = open(self.srcname, "rb")
        writtenData = fp.read()
        fp.close()
        
        for file in (self.zipname, tempfile.TemporaryFile(), StringIO.StringIO()):
            zipTest(self.srcname, file, zipfile.ZIP_STORED, writtenData)
        
        for file in (self.zipname, tempfile.TemporaryFile(), StringIO.StringIO()):
            zipTest(self.srcname, file, zipfile.ZIP_DEFLATED, writtenData)

    def test_delete(self):
        fp = open(self.srcname, "wb")               # Make a source file with some lines
        for i in range(0, 1000):
            fp.write("Test of zipfile line %d.\n" % i)
        fp.close()
        
        fp = open(self.srcname, "rb")
        writtenData = fp.read()
        fp.close()
        
        for file in (self.zipname, tempfile.TemporaryFile(), StringIO.StringIO()):
            deleteTest(self.srcname, file, zipfile.ZIP_STORED, writtenData)
        
        for file in (self.zipname, tempfile.TemporaryFile(), StringIO.StringIO()):
            deleteTest(self.srcname, file, zipfile.ZIP_DEFLATED, writtenData)

    def test_closes(self):
        # This test checks that the ZipFile constructor closes the file object
        # it opens if there's an error in the file.  If it doesn't, the traceback
        # holds a reference to the ZipFile object and, indirectly, the file object.
        # On Windows, this causes the os.unlink() call to fail because the
        # underlying file is still open.  This is SF bug #412214.
        #
        fp = open(self.srcname, "w")
        fp.write("this is not a legal zip file\n")
        fp.close()
        try:
            zf = zipfileext.ZipFileExt(self.srcname)
        except zipfile.BadZipfile:
            os.unlink(self.srcname)

    def test_403871(self):
        # make sure we don't raise an AttributeError when a partially-constructed
        # ZipFile instance is finalized; this tests for regression on SF tracker
        # bug #403871.
        try:
            zipfileext.ZipFileExt(self.srcname)
        except IOError:
            # The bug we're testing for caused an AttributeError to be raised
            # when a ZipFile instance was created for a file that did not
            # exist; the .fp member was not initialized but was needed by the
            # __del__() method.  Since the AttributeError is in the __del__(),
            # it is ignored, but the user should be sufficiently annoyed by
            # the message on the output that regression will be noticed
            # quickly.
            pass
        else:
            raise TestFailed("expected creation of readable ZipFile without\n"
                             "  a file to raise an IOError.")

    def test_closedthrow(self):
        # Verify that testzip() doesn't swallow inappropriate exceptions.
        data = StringIO.StringIO()
        zipf = zipfileext.ZipFileExt(data, mode="w")
        zipf.writestr("foo.txt", "O, for a Muse of Fire!")
        zipf.close()
        zipf = zipfileext.ZipFileExt(data, mode="r")
        zipf.close()
        try:
            zipf.testzip()
        except RuntimeError:
            # This is correct; calling .read on a closed ZipFile should throw
            # a RuntimeError, and so should calling .testzip.  An earlier
            # version of .testzip would swallow this exception (and any other)
            # and report that the first file in the archive was corrupt.
            pass
        else:
            raise TestFailed("expected calling .testzip on a closed ZipFile"
                             " to raise a RuntimeError")
        del data, zipf

