import os
import unittest

from nose.plugins import PluginTester

support = os.path.join(os.path.dirname(__file__), 'support', 'issue513')

class TestPrintedTraceback(PluginTester, unittest.TestCase):
    args = ['--where='+support]
    activate = "-v"

    def makeSuite(self):
        # make PluginTester happy, because we don't specify suitepath, we
        # have to implement this function
        return None

    def test_correct_exception_raised(self):
        print
        print '!' * 70
        print str(self.output)
        print '!' * 70
        print

        # Look for the line in the traceback causing the failure
        assert "raise '\\xf1'.encode('ASCII')" in str(self.output)
        assert 'FAILED (errors=1)' in str(self.output)

if __name__ == '__main__':
    unittest.main()
