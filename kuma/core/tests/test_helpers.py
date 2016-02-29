# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime

import pytest
import pytz
from babel.dates import format_date, format_datetime, format_time
from django.test import RequestFactory
from django.utils import timezone
from pyquery import PyQuery as pq
from soapbox.models import Message

from kuma.core.tests import KumaTestCase, eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

from ..exceptions import DateTimeFormatError
from ..templatetags.jinja_helpers import (datetimeformat, get_soapbox_messages,
                                          jsonencode, number, soapbox_messages,
                                          timesince, urlencode, yesno)


class TestHelpers(KumaTestCase):

    def test_number(self):
        context = {'request': namedtuple('R', 'LANGUAGE_CODE')('en-US')}
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
        eq_('', timesince(datetime(9999, 1, 2,
                                   tzinfo=timezone.get_default_timezone())))


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
        m = Message(message='Global', is_global=True, is_active=True, url='/')
        m.save()
        eq_(m.message, get_soapbox_messages('/')[0].message)
        eq_(m.message, get_soapbox_messages('/en-US/')[0].message)

    def test_subsection_message(self):
        m = Message(message='Search down', is_global=False, is_active=True,
                    url='/search')
        m.save()
        eq_(0, len(get_soapbox_messages('/')))
        eq_(0, len(get_soapbox_messages('/docs')))
        eq_(0, len(get_soapbox_messages('/en-US/docs')))
        eq_(m.message, get_soapbox_messages('/en-US/search')[0].message)
        eq_(m.message, get_soapbox_messages('/de/search')[0].message)

    def test_message_with_url_is_link(self):
        m = Message(message='Go to http://bit.ly/sample-demo', is_global=True,
                    is_active=True, url='/')
        m.save()
        ok_('Go to <a href="http://bit.ly/sample-demo">'
            'http://bit.ly/sample-demo</a>' in
            soapbox_messages(get_soapbox_messages('/')))


class TestDateTimeFormat(UserTestCase):
    def setUp(self):
        super(TestDateTimeFormat, self).setUp()
        self.default_timezone = timezone.get_default_timezone()
        self.old_times = datetime(2010, 5, 8).replace(
            tzinfo=self.default_timezone)
        url_ = reverse('home')
        self.context = {'request': RequestFactory().get(url_)}
        self.context['request'].LANGUAGE_CODE = u'en-US'
        self.context['request'].user = self.user_model.objects.get(
            username='testuser01')

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = timezone.now()
        value_returned = unicode(datetimeformat(self.context, date_today))
        value_expected = 'Today at %s' % format_time(date_today,
                                                     format='short',
                                                     tzinfo=self.default_timezone,
                                                     locale=u'en_US')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context['request'].LANGUAGE_CODE = u'fr'
        value_expected = format_datetime(self.old_times,
                                         format='short',
                                         tzinfo=self.default_timezone,
                                         locale=u'fr')
        value_returned = datetimeformat(self.context, self.old_times)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_default(self):
        """Expects shortdatetime."""
        value_expected = format_datetime(self.old_times,
                                         format='short',
                                         tzinfo=self.default_timezone,
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, self.old_times)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_longdatetime(self):
        """Expects long format."""
        value_expected = format_datetime(self.old_times,
                                         format='long',
                                         tzinfo=self.default_timezone,
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, self.old_times,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_date(self):
        """Expects date format."""
        value_expected = format_date(self.old_times,
                                     locale=u'en_US')
        value_returned = datetimeformat(self.context, self.old_times,
                                        format='date')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_time(self):
        """Expects time format."""
        value_expected = format_time(self.old_times,
                                     tzinfo=self.default_timezone,
                                     locale=u'en_US')
        value_returned = datetimeformat(self.context, self.old_times,
                                        format='time')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        value_expected = format_datetime(self.old_times,
                                         tzinfo=self.default_timezone,
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, self.old_times,
                                        format='datetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = timezone.now()
        with pytest.raises(DateTimeFormatError):
            datetimeformat(self.context, date_today, format='unknown')

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        with pytest.raises(ValueError):
            datetimeformat(self.context, 'invalid')

    def test_json_helper(self):
        eq_('false', jsonencode(False))
        eq_('{"foo": "bar"}', jsonencode({'foo': 'bar'}))

    def test_user_timezone(self):
        """Shows time in user timezone."""
        # Choose user with non default timezone
        user = self.user_model.objects.get(username='admin')
        self.context['request'].user = user

        # Convert tzvalue to user timezone
        user_tz = pytz.timezone(user.timezone)
        tzvalue = self.old_times.astimezone(user_tz)

        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, self.old_times,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)
