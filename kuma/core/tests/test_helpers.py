# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime

import bitly_api
import jingo
import mock
from nose.tools import eq_, ok_, assert_raises

from django.conf import settings
from django.test import RequestFactory

from babel.dates import format_date, format_time, format_datetime
from pyquery import PyQuery as pq
from pytz import timezone
from soapbox.models import Message

from kuma.core.cache import memcache
from kuma.core.helpers import bitly_shorten, bitly
from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

from ..exceptions import DateTimeFormatError
from ..helpers import (timesince, yesno, urlencode,
                       soapbox_messages, get_soapbox_messages,
                       datetimeformat, jsonencode, number)


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


class TestHelpers(KumaTestCase):

    def setUp(self):
        jingo.load_helpers()

    def test_number(self):
        context = {'request': namedtuple('R', 'locale')('en-US')}
        eq_('5,000', number(context, 5000))
        eq_('', number(context, None))

    def test_yesno(self):
        eq_('Yes', yesno(True))
        eq_('No', yesno(False))
        eq_('Yes', yesno(1))
        eq_('No', yesno(0))


class TimesinceTests(KumaTestCase):
    """Tests for the timesince filter"""

    def test_none(self):
        """If None is passed in, timesince returns ''."""
        eq_('', timesince(None))

    def test_trunc(self):
        """Assert it returns only the most significant time division."""
        eq_('1 year ago',
            timesince(datetime(2000, 1, 2), now=datetime(2001, 2, 3)))

    def test_future(self):
        """
        Test behavior when date is in the future and also when omitting the
        now kwarg.
        """
        eq_('', timesince(datetime(9999, 1, 2)))


class TestUrlEncode(KumaTestCase):

    def test_utf8_urlencode(self):
        """Bug 689056: Unicode strings with non-ASCII characters should not
        throw a KeyError when filtered through URL encoding"""
        try:
            s = u"Someguy Dude\xc3\xaas Lastname"
            urlencode(s)
        except KeyError:
            self.fail("There should be no KeyError")


class TestSoapbox(KumaTestCase):

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

    def test_message_with_url_is_link(self):
        m = Message(message="Go to http://bit.ly/sample-demo", is_global=True,
                    is_active=True, url="/")
        m.save()
        ok_('Go to <a href="http://bit.ly/sample-demo">'
            'http://bit.ly/sample-demo</a>' in
            soapbox_messages(get_soapbox_messages("/")))


class TestDateTimeFormat(UserTestCase):
    def setUp(self):
        super(TestDateTimeFormat, self).setUp()
        url_ = reverse('home')
        self.context = {'request': RequestFactory().get(url_)}
        self.context['request'].locale = u'en-US'
        self.context['request'].user = self.user_model.objects.get(username='testuser01')

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.today()
        value_returned = unicode(datetimeformat(self.context, date_today))
        value_expected = 'Today at %s' % format_time(date_today,
                                                     format='short',
                                                     locale=u'en_US')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context['request'].locale = u'fr'
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'fr')
        value_returned = datetimeformat(self.context, value_test)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_default(self):
        """Expects shortdatetime."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_longdatetime(self):
        """Expects long format."""
        value_test = datetime.fromordinal(733900)
        tzvalue = timezone(settings.TIME_ZONE).localize(value_test)
        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_date(self):
        """Expects date format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='date')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_time(self):
        """Expects time format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_time(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='time')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='datetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.today()
        assert_raises(DateTimeFormatError, datetimeformat, self.context,
                      date_today, format='unknown')

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        assert_raises(ValueError, datetimeformat, self.context, 'invalid')

    def test_json_helper(self):
        eq_('false', jsonencode(False))
        eq_('{"foo": "bar"}', jsonencode({'foo': 'bar'}))

    def test_user_timezone(self):
        """Shows time in user timezone."""
        value_test = datetime.fromordinal(733900)
        # Choose user with non default timezone
        user = self.user_model.objects.get(username='admin')
        self.context['request'].user = user

        # Convert tzvalue to user timezone
        default_tz = timezone(settings.TIME_ZONE)
        user_tz = user.profile.timezone
        tzvalue = default_tz.localize(value_test)
        tzvalue = user_tz.normalize(tzvalue.astimezone(user_tz))

        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)


class BitlyTestCase(KumaTestCase):
    @mock.patch.object(memcache, 'set')  # prevent caching
    @mock.patch.object(bitly, 'shorten')
    def test_bitly_shorten(self, shorten, cache_set):
        long_url = 'http://example.com/long-url'
        short_url = 'http://bit.ly/short-url'

        # the usual case of returning a dict with a URL
        def short_mock(*args, **kwargs):
            return {'url': short_url}
        shorten.side_effect = short_mock

        eq_(bitly_shorten(long_url), short_url)
        shorten.assert_called_with(long_url)

        # in case of a key error
        def short_mock(*args, **kwargs):
            return {}
        shorten.side_effect = short_mock
        eq_(bitly_shorten(long_url), long_url)
        shorten.assert_called_with(long_url)

        # in case of an upstream error
        shorten.side_effect = bitly_api.BitlyError('500', 'fail fail fail')
        eq_(bitly_shorten(long_url), long_url)
