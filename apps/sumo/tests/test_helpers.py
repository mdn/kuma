# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User

from nose.tools import eq_
from nose.tools import assert_raises
import test_utils
import jingo
from babel.dates import format_date, format_time, format_datetime
from pytz import timezone
from pyquery import PyQuery as pq

from sumo.helpers import (profile_url, profile_avatar, datetimeformat,
                          DateTimeFormatError, collapse_linebreaks)
from sumo.urlresolvers import reverse


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


class TestHelpers(TestCase):

    def setUp(self):
        jingo.load_helpers()

    def test_fe_helper(self):
        context = {'var': '<bad>'}
        template = '{{ "<em>{t}</em>"|fe(t=var) }}'
        eq_('<em>&lt;bad&gt;</em>', render(template, context))

    def test_fe_positional(self):
        context = {'var': '<bad>'}
        template = '{{ "<em>{0}</em>"|fe(var) }}'
        eq_('<em>&lt;bad&gt;</em>', render(template, context))

    def test_fe_unicode(self):
        context = {'var': u'Français'}
        template = '{{ "Speak {0}"|fe(var) }}'
        eq_(u'Speak Français', render(template, context))

    def test_urlparams_unicode(self):
        context = {'var': u'Fran\xc3\xa7ais'}
        template = '{{ url("search")|urlparams(q=var) }}'
        eq_(u'/en-US/search?q=Fran%C3%A7ais', render(template, context))

    def test_urlparams_valid(self):
        context = {'a': 'foo', 'b': 'bar'}
        template = '{{ "/search"|urlparams(a=a, b=b) }}'
        eq_(u'/search?a=foo&amp;b=bar', render(template, context))

    def test_profile_url(self):
        user = User.objects.create(pk=500000, username=u'testuser')
        eq_(u'/tiki-user_information.php?locale=en-US&userId=500000',
            profile_url(user))

    def test_profile_avatar(self):
        user = User.objects.create(pk=500001, username=u'testuser2')
        eq_(u'/tiki-show_user_avatar.php?user=testuser2',
            profile_avatar(user))

    def test_collapse_linebreaks(self):
        """Make sure collapse_linebreaks works on some tricky cases."""
        eq_(collapse_linebreaks('\r\n \t  \n\r  Trouble\r\n\r\nshooting \r\n'),
            '\r\n  Trouble\r\nshooting\r\n')
        eq_(collapse_linebreaks('Application Basics\n      \n\n      \n      '
                                '\n\n\n        \n          \n            \n   '
                                '           Name'),
                                'Application Basics\r\n              Name')


class TestDateTimeFormat(TestCase):

    def setUp(self):
        url = reverse('forums.threads', args=[u'testslug'])
        self.context = {'request': test_utils.RequestFactory().get(url)}
        self.context['request'].locale = u'en-US'

    def test_today(self):
        """Expects shortdatetime, format: Today at {time}."""
        date_today = datetime.datetime.today()
        value_returned = unicode(datetimeformat(self.context, date_today))
        value_expected = 'Today at %s' % format_time(date_today,
                                                     format='short',
                                                     locale=u'en_US')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_locale(self):
        """Expects shortdatetime in French."""
        self.context['request'].locale = u'fr'
        value_test = datetime.datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'fr')
        value_returned = datetimeformat(self.context, value_test)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_default(self):
        """Expects shortdatetime."""
        value_test = datetime.datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, format='short',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test)
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_longdatetime(self):
        """Expects long format."""
        value_test = datetime.datetime.fromordinal(733900)
        tzvalue = timezone(settings.TIME_ZONE).localize(value_test)
        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_date(self):
        """Expects date format."""
        value_test = datetime.datetime.fromordinal(733900)
        value_expected = format_date(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='date')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_time(self):
        """Expects time format."""
        value_test = datetime.datetime.fromordinal(733900)
        value_expected = format_time(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='time')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_datetime(self):
        """Expects datetime format."""
        value_test = datetime.datetime.fromordinal(733900)
        value_expected = format_datetime(value_test, locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='datetime')
        eq_(pq(value_returned)('time').text(), value_expected)

    def test_unknown_format(self):
        """Unknown format raises DateTimeFormatError."""
        date_today = datetime.datetime.today()
        assert_raises(DateTimeFormatError, datetimeformat, self.context,
                      date_today, format='unknown')

    def test_invalid_value(self):
        """Passing invalid value raises ValueError."""
        assert_raises(ValueError, datetimeformat, self.context, 'invalid')
