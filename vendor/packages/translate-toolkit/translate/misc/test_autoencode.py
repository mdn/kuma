#!/usr/bin/env python

from translate.misc import autoencode
from py import test

class TestAutoencode:
    type2test = autoencode.autoencode

    def test_default_encoding(self):
        """tests that conversion to string uses the encoding attribute"""
        s = self.type2test(u'unicode string', 'utf-8')
        assert s.encoding == 'utf-8'
        assert str(s) == 'unicode string'
        s = self.type2test(u'\u20ac')
        assert str(self.type2test(u'\u20ac', 'utf-8')) == '\xe2\x82\xac'

    def test_uniqueness(self):
        """tests constructor creates unique objects"""
        s1 = unicode(u'unicode string')
        s2 = unicode(u'unicode string')
        assert s1 == s2
        assert s1 is s2
        s1 = self.type2test(u'unicode string', 'utf-8')
        s2 = self.type2test(u'unicode string', 'ascii')
        s3 = self.type2test(u'unicode string', 'utf-8')
        assert s1 == s2 == s3
        assert s1 is not s2
        # even though all the attributes are the same, this is a mutable type
        # so the objects created must be different
        assert s1 is not s3

    def test_bad_encoding(self):
        """tests that we throw an exception if we don't know the encoding"""
        assert test.raises(ValueError, self.type2test, 'text', 'some-encoding')
