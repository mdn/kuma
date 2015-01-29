# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime
from os.path import basename, getsize, isfile
from glob import glob
import re

import jingo
from nose.tools import eq_, ok_, assert_raises
import test_utils


from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.templatetags.static import static
from django.test import RequestFactory

from babel.dates import format_date, format_time, format_datetime
from pyquery import PyQuery as pq
from pytz import timezone
from soapbox.models import Message

from kuma.users.tests import UserTestCase
from kuma.core.urlresolvers import reverse


from ..exceptions import DateTimeFormatError
from ..helpers import (timesince, urlparams, yesno, urlencode,
                       soapbox_messages, get_soapbox_messages,
                       datetimeformat, jsonencode, number, cache_bust)


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


class TestHelpers(test_utils.TestCase):

    def setUp(self):
        jingo.load_helpers()

    def test_number(self):
        context = {'request': namedtuple('R', 'locale')('en-US')}
        eq_('5,000', number(context, 5000))
        eq_('', number(context, None))

    def test_urlparams_unicode(self):
        context = {'q': u'Français'}
        eq_(u'/foo?q=Fran%C3%A7ais', urlparams('/foo', **context))
        context['q'] = u'\u0125help'
        eq_(u'/foo?q=%C4%A5help', urlparams('/foo', **context))

    def test_urlparams_valid(self):
        context = {'a': 'foo', 'b': 'bar'}
        eq_(u'/foo?a=foo&b=bar', urlparams('/foo', **context))

    def test_urlparams_query_string(self):
        eq_(u'/foo?a=foo&b=bar', urlparams('/foo?a=foo', b='bar'))

    def test_urlparams_multivalue(self):
        eq_(u'/foo?a=foo&a=bar', urlparams('/foo?a=foo&a=bar'))
        eq_(u'/foo?a=bar', urlparams('/foo?a=foo', a='bar'))

    def test_urlparams_none(self):
        """Assert a value of None doesn't make it into the query string."""
        eq_(u'/foo', urlparams('/foo', bar=None))

    def test_yesno(self):
        eq_('Yes', yesno(True))
        eq_('No', yesno(False))
        eq_('Yes', yesno(1))
        eq_('No', yesno(0))

    def test_cache_bust(self):
        context = {'request': namedtuple('R', 'locale')('en-US')}
        manifest = 'build/rev-manifest.json'

        ok_(isfile(manifest))
        ok_(getsize(manifest) > 0)

        # Test the case of a match being found
        versioned_scripts = glob('build/js/*.js')
        versioned_script = basename(
            versioned_scripts[len(versioned_scripts) / 2]
        )
        unversioned_script = re.sub('-min-.*\.js', '-min.js', versioned_script)
        eq_(cache_bust(context, 'js/' + unversioned_script),
            static('js/' + versioned_script))

        # Test the case of a match not being found
        eq_(cache_bust(context, 'js/_test.js'), static('js/_test.js'))


class TimesinceTests(test_utils.TestCase):
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


class TestUrlEncode(test_utils.TestCase):

    def test_utf8_urlencode(self):
        """Bug 689056: Unicode strings with non-ASCII characters should not
        throw a KeyError when filtered through URL encoding"""
        try:
            s = u"Someguy Dude\xc3\xaas Lastname"
            urlencode(s)
        except KeyError:
            self.fail("There should be no KeyError")


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
        self.context['request'].user = User.objects.get(username='testuser01')

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
        user = User.objects.get(username='admin')
        self.context['request'].user = user

        # Convert tzvalue to user timezone
        default_tz = timezone(settings.TIME_ZONE)
        user_tz = user.get_profile().timezone
        tzvalue = default_tz.localize(value_test)
        tzvalue = user_tz.normalize(tzvalue.astimezone(user_tz))

        value_expected = format_datetime(tzvalue, format='long',
                                         locale=u'en_US')
        value_returned = datetimeformat(self.context, value_test,
                                        format='longdatetime')
        eq_(pq(value_returned)('time').text(), value_expected)
