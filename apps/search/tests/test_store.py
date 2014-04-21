from __future__ import absolute_import
from base64 import b64decode
from nose.tools import raises, eq_
from test_utils import TestCase
from search.store import referrer_url


class MockRequest(object):
    pass


class StoreTests(TestCase):

    def test_bug_990607(self):
        """bug 990607: referer_url fails on strangely encoded referers"""

        # HACK: Having trouble getting the exact awkward encoding from the
        # header. This is the result of copying from the browser, then 
        # `pbpaste | base64`. But, it reproduces the error, at least. I suspect
        # the problem is a mashed up encoding between ISO-8859 and UTF-8
        problematic_referer = b64decode("""
            aHR0cDovL2RldmVsb3Blci5tb3ppbGxhLm9yZy9mci9kb2NzL0phdmFTY3Jpc
            HQvUsODwqlmw4PCqXJlbmNlX0phdmFTY3JpcHQvUsODwqlmw4PCqXJlbmNlX0
            phdmFTY3JpcHQvT2JqZXRzX2dsb2JhdXgvRGF0ZS9wYXJzZQ==
        """)
        
        req = MockRequest()
        req.locale = 'en-US'
        req.META = dict(HTTP_REFERER=problematic_referer)

        result = referrer_url(req)
        eq_(result, None)
