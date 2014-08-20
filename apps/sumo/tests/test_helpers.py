# -*- coding: utf-8 -*-
from collections import namedtuple
from datetime import datetime

from django.conf import settings
from django.forms.fields import CharField

from babel.dates import format_date, format_time, format_datetime
import jingo
from nose.tools import eq_, assert_raises
from pytz import timezone
from pyquery import PyQuery as pq
import test_utils

from sumo.helpers import (datetimeformat, DateTimeFormatError,
                          collapse_linebreaks, url, json, timesince,
                          label_with_help, urlparams, yesno, number)
from sumo.tests import TestCase
from sumo.urlresolvers import reverse


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


class TestHelpers(TestCase):

    def setUp(self):
        jingo.load_helpers()

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

    def test_collapse_linebreaks(self):
        """Make sure collapse_linebreaks works on some tricky cases."""
        eq_(collapse_linebreaks('\r\n \t  \n\r  Trouble\r\n\r\nshooting \r\n'),
            '\r\n  Trouble\r\nshooting\r\n')
        eq_(collapse_linebreaks('Application Basics\n      \n\n      \n      '
                                '\n\n\n        \n          \n            \n   '
                                '           Name'),
                                'Application Basics\r\n              Name')

    def test_label_with_help(self):
        field = CharField(label='Foo', help_text='Foo bar')
        field.auto_id = 'foo'
        expect = '<label for="foo" title="Foo bar">Foo</label>'
        eq_(expect, label_with_help(field))

    def test_yesno(self):
        eq_('Yes', yesno(True))
        eq_('No', yesno(False))
        eq_('Yes', yesno(1))
        eq_('No', yesno(0))

    def test_number(self):
        context = {'request': namedtuple('R', 'locale')('en-US')}
        eq_('5,000', number(context, 5000))
        eq_('', number(context, None))


class TimesinceTests(TestCase):
    """Tests for the timesince filter"""

    def test_none(self):
        """If None is passed in, timesince returns ''."""
        eq_('', timesince(None))

    def test_trunc(self):
        """Assert it returns only the most significant time division."""
        eq_('1 year ago',
            timesince(datetime(2000, 1, 2), now=datetime(2001, 2, 3)))

    def test_future(self):
        """Test behavior when date is in the future and also when omitting the
        `now` kwarg."""
        eq_('', timesince(datetime(9999, 1, 2)))
