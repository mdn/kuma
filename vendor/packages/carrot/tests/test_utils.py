import unittest

from carrot import utils


class TestUtils(unittest.TestCase):

    def test_partition_unicode(self):
        s = u'hi mom'
        self.assertEqual(utils.partition(s, ' '), (u'hi', u' ', u'mom'))

    def test_rpartition_unicode(self):
        s = u'hi mom !'
        self.assertEqual(utils.rpartition(s, ' '), (u'hi mom', u' ', u'!'))
