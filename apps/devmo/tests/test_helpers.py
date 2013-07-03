# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_
import test_utils
from soapbox.models import Message

from devmo.helpers import urlencode, get_soapbox_messages, datetimeformat


class TestUrlEncode(test_utils.TestCase):

    def test_utf8_urlencode(self):
        """Bug 689056: Unicode strings with non-ASCII characters should not
        throw a KeyError when filtered through URL encoding"""
        try:
            s = u"Someguy Dude\xc3\xaas Lastname"
            urlencode(s)
        except KeyError:
            ok_(False, "There should be no KeyError")


class TestDateTimeFormat(test_utils.TestCase):

    def test_utf8_urlencode(self):
        s = u"2013-05-20T15:06:45"
        eq_('2013-05-20', datetimeformat(s))


class TestSoapbox(test_utils.TestCase):

    def test_global_message(self):
        m = Message(message="Global", is_global=True, is_active=True, url="/")
        m.save()
        eq_(m.message, get_soapbox_messages("/")[0].message)
        eq_(m.message, get_soapbox_messages("/en-US/")[0].message)
        eq_(m.message, get_soapbox_messages("/fr/demos/")[0].message)

    def test_subsection_message(self):
        m = Message(message="Derby", is_global=False, is_active=True,
                    url="/demos/devderby")
        m.save()
        eq_(0, len(get_soapbox_messages("/")))
        eq_(0, len(get_soapbox_messages("/demos")))
        eq_(0, len(get_soapbox_messages("/en-US/demos")))
        eq_(m.message, get_soapbox_messages(
            "/en-US/demos/devderby")[0].message)
        eq_(m.message, get_soapbox_messages("/de/demos/devderby")[0].message)
