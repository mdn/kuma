import unittest

class TestIssue135(unittest.TestCase):
    def test_issue135(self):
        print "something"
        raise KeyError("fake")