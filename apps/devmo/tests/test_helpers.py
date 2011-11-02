import logging
import urllib2

from mock import patch
from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr
import test_utils

from devmo.helpers import urlencode


class TestUrlEncode(test_utils.TestCase):

    def test_utf8_urlencode(self):
        """Bug 689056: Unicode strings with non-ASCII characters should not
        throw a KeyError when filtered through URL encoding"""
        try:
            s = u"Someguy Dude\xc3\xaas Lastname"
            u = urlencode(s)
        except KeyError:
            ok_(False, "There should be no KeyError")
