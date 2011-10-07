import logging

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr
import test_utils

from devmo.helpers import devmo_url, urlencode


class UrlencodeTest(test_utils.TestCase):

    def test_unicode_bug689206(self):
        try:
            s = u"test\xader"
            u = urlencode(s)
        except KeyError, e:
            ok_(False, "urlencode should not throw KeyError")
