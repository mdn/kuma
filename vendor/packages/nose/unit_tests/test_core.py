import os
import sys
import unittest
from cStringIO import StringIO
from optparse import OptionParser
import nose.core
from nose.config import Config
from nose.tools import set_trace
from mock import Bucket, MockOptParser


class NullLoader:
    def loadTestsFromNames(self, names):
        return unittest.TestSuite()

class TestAPI_run(unittest.TestCase):

    def test_restore_stdout(self):
        print "AHOY"
        s = StringIO()
        print s
        stdout = sys.stdout
        conf = Config(stream=s)
        # set_trace()
        print "About to run"
        res = nose.core.run(
            testLoader=NullLoader(), argv=['test_run'], env={}, config=conf)
        print "Done running"
        stdout_after = sys.stdout
        self.assertEqual(stdout, stdout_after)

class Undefined(object):
    pass

class TestUsage(unittest.TestCase):

    def test_from_directory(self):
        usage_txt = nose.core.TestProgram.usage()
        assert usage_txt.startswith('nose collects tests automatically'), (
                "Unexpected usage: '%s...'" % usage_txt[0:50].replace("\n", '\n'))

    def test_from_zip(self):
        requested_data = []

        # simulates importing nose from a zip archive
        # with a zipimport.zipimporter instance
        class fake_zipimporter(object):

            def get_data(self, path):
                requested_data.append(path)
                # Return as str in Python 2, bytes in Python 3.
                return '<usage>'.encode('utf-8')

        existing_loader = getattr(nose, '__loader__', Undefined)
        try:
            nose.__loader__ = fake_zipimporter()
            usage_txt = nose.core.TestProgram.usage()
            self.assertEqual(usage_txt, '<usage>')
            self.assertEqual(requested_data, [os.path.join(
                os.path.dirname(nose.__file__), 'usage.txt')])
        finally:
            if existing_loader is not Undefined:
                nose.__loader__ = existing_loader
            else:
                del nose.__loader__

if __name__ == '__main__':
    unittest.main()
