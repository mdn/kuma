import os
import unittest

from nose.plugins import Plugin, PluginTester
#from nose.plugins.builtin import FailureDetail, Capture, Doctest

support = os.path.join(os.path.dirname(__file__), 'support', 'issue408')

class TestIssue408(PluginTester, unittest.TestCase):
    args = ['--where='+support, 'test:testa.test1', 'test:testa.test2', 'test:testb.test1', 'test:testb.test2']
    activate = "-v"

    def makeSuite(self):
        # make PluginTester happy, because we don't specify suitepath, we
        # have to implement this function
        return None

    def test_no_failure(self):
        output = str(self.output)
        assert 'FAIL:' not in output
        assert 'AssertionError' not in output
        assert 'OK' in output

if __name__ == '__main__':
    unittest.main()
