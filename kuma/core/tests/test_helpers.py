# -*- coding: utf-8 -*-
from datetime import datetime

import mock
import pytest
import pytz
from babel.dates import format_date, format_datetime, format_time
from django.conf import settings
from django.test import RequestFactory, override_settings
from soapbox.models import Message

from kuma.core.tests import KumaTestCase, eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

from ..exceptions import DateTimeFormatError
from ..templatetags.jinja_helpers import (datetimeformat, get_soapbox_messages,
                                          in_utc, jsonencode, soapbox_messages,
                                          yesno)


class TestYesNo(KumaTestCase):

    def test_yesno(self):
        eq_('Yes', yesno(True))
        eq_('No', yesno(False))
        eq_('Yes', yesno(1))
        eq_('No', yesno(0))


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
        url_ = reverse('home')
        self.context = {'request': RequestFactory().get(url_)}
        self.context['request'].LANGUAGE_CODE = u'en-US'
        self.context['request'].user = self.user_model.objects.get(username='testuser01')

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.today()
        value_expected = 'Today at %s' % format_time(date_today,
                                                     format='short',
                                                     locale=u'en_US')
        value_returned = datetimeformat(self.context, date_today,
                                        output='json')
        eq_(value_returned, value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context['request'].LANGUAGE_CODE = u'fr'
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'fr')
        value_returned = datetimeformat(self.context, value_test,
                                        output='json')
        eq_(value_returned, value_expected)

    def test_default(self):
        """Expects shortdatetime."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        output='json')
        eq_(value_returned, value_expected)

    def test_longdatetime(self):
        """Expects long format."""
        value_test = datetime.fromordinal(733900)
        tzvalue = pytz.timezone(settings.TIME_ZONE).localize(value_test)
        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime',
                                        output='json')
        eq_(value_returned, value_expected)

    def test_date(self):
        """Expects date format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='date',
                                        output='json')
        eq_(value_returned, value_expected)

    def test_time(self):
        """Expects time format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_time(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='time',
                                        output='json')
        eq_(value_returned, value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        value_test = datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='datetime',
                                        output='json')
        eq_(value_returned, value_expected)

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.today()
        with pytest.raises(DateTimeFormatError):
            datetimeformat(self.context, date_today, format='unknown')

    @mock.patch('babel.dates.format_datetime')
    def test_broken_format(self, mocked_format_datetime):
        value_test = datetime.fromordinal(733900)
        value_english = format_datetime(value_test, locale=u'en_US')
        self.context['request'].LANGUAGE_CODE = u'fr'
        mocked_format_datetime.side_effect = [
            # first call is returning a KeyError as if the format is broken
            KeyError,
            # second call returns the English fallback version as expected
            value_english,
        ]
        value_returned = datetimeformat(self.context, value_test,
                                        format='datetime',
                                        output='json')
        eq_(value_returned, value_english)

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        with pytest.raises(ValueError):
            datetimeformat(self.context, 'invalid')

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
        default_tz = pytz.timezone(settings.TIME_ZONE)
        user_tz = pytz.timezone(user.timezone)
        tzvalue = default_tz.localize(value_test)
        tzvalue = user_tz.normalize(tzvalue.astimezone(user_tz))

        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime',
                                        output='json')
        eq_(value_returned, value_expected)


class TestInUtc(KumaTestCase):
    """Test the in_utc datetime filter."""
    def test_utc(self):
        """Assert a time in UTC remains in UTC."""
        dt = datetime(2016, 3, 10, 16, 12, tzinfo=pytz.utc)
        out = in_utc(dt)
        assert out == dt

    def test_aware(self):
        """Assert a time in a different time zone is converted to UTC."""
        hour = 10
        dt = datetime(2016, 3, 10, hour, 14)
        dt = pytz.timezone('US/Central').localize(dt)
        out = in_utc(dt)
        assert out == datetime(2016, 3, 10, hour + 6, 14, tzinfo=pytz.utc)

    @override_settings(TIME_ZONE='US/Pacific')
    def test_naive(self):
        """Assert that naïve datetimes are first converted to system time."""
        hour = 8
        dt = datetime(2016, 3, 10, hour, 8)
        out = in_utc(dt)
        assert out == datetime(2016, 3, 10, hour + 8, 8, tzinfo=pytz.utc)
