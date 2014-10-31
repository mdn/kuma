# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

from datetime import date, datetime, time
import doctest
import unittest

from pytz import timezone

from babel import dates


class DateTimeFormatTestCase(unittest.TestCase):

    def test_quarter_format(self):
        d = date(2006, 6, 8)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('2', fmt['Q'])
        self.assertEqual('2nd quarter', fmt['QQQQ'])
        d = date(2006, 12, 31)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('Q4', fmt['QQQ'])

    def test_month_context(self):
        d = date(2006, 1, 8)
        fmt = dates.DateTimeFormat(d, locale='cs_CZ')
        self.assertEqual('1', fmt['MMM'])
        fmt = dates.DateTimeFormat(d, locale='cs_CZ')
        self.assertEqual('1.', fmt['LLL'])

    def test_abbreviated_month_alias(self):
        d = date(2006, 3, 8)
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual(u'Mär', fmt['LLL'])

    def test_week_of_year_first(self):
        d = date(2006, 1, 8)
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('1', fmt['w'])
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('02', fmt['ww'])

    def test_week_of_year_first_with_year(self):
        d = date(2006, 1, 1)
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('52', fmt['w'])
        self.assertEqual('2005', fmt['YYYY'])

    def test_week_of_year_last(self):
        d = date(2005, 12, 26)
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('52', fmt['w'])
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('53', fmt['ww'])

    def test_week_of_month_first(self):
        d = date(2006, 1, 8)
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('1', fmt['W'])
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('2', fmt['W'])

    def test_week_of_month_last(self):
        d = date(2006, 1, 29)
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('4', fmt['W'])
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('5', fmt['W'])

    def test_day_of_year(self):
        d = date(2007, 4, 1)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('91', fmt['D'])

    def test_day_of_year_first(self):
        d = date(2007, 1, 1)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('001', fmt['DDD'])

    def test_day_of_year_last(self):
        d = date(2007, 12, 31)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('365', fmt['DDD'])

    def test_day_of_week_in_month(self):
        d = date(2007, 4, 15)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('3', fmt['F'])

    def test_day_of_week_in_month_first(self):
        d = date(2007, 4, 1)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('1', fmt['F'])

    def test_day_of_week_in_month_last(self):
        d = date(2007, 4, 29)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('5', fmt['F'])

    def test_local_day_of_week(self):
        d = date(2007, 4, 1) # a sunday
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('7', fmt['e']) # monday is first day of week
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('01', fmt['ee']) # sunday is first day of week
        fmt = dates.DateTimeFormat(d, locale='dv_MV')
        self.assertEqual('03', fmt['ee']) # friday is first day of week

        d = date(2007, 4, 2) # a monday
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('1', fmt['e']) # monday is first day of week
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('02', fmt['ee']) # sunday is first day of week
        fmt = dates.DateTimeFormat(d, locale='dv_MV')
        self.assertEqual('04', fmt['ee']) # friday is first day of week

    def test_local_day_of_week_standalone(self):
        d = date(2007, 4, 1) # a sunday
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('7', fmt['c']) # monday is first day of week
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('1', fmt['c']) # sunday is first day of week
        fmt = dates.DateTimeFormat(d, locale='dv_MV')
        self.assertEqual('3', fmt['c']) # friday is first day of week

        d = date(2007, 4, 2) # a monday
        fmt = dates.DateTimeFormat(d, locale='de_DE')
        self.assertEqual('1', fmt['c']) # monday is first day of week
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('2', fmt['c']) # sunday is first day of week
        fmt = dates.DateTimeFormat(d, locale='dv_MV')
        self.assertEqual('4', fmt['c']) # friday is first day of week

    def test_fractional_seconds(self):
        t = time(15, 30, 12, 34567)
        fmt = dates.DateTimeFormat(t, locale='en_US')
        self.assertEqual('3457', fmt['SSSS'])

    def test_fractional_seconds_zero(self):
        t = time(15, 30, 0)
        fmt = dates.DateTimeFormat(t, locale='en_US')
        self.assertEqual('0000', fmt['SSSS'])

    def test_milliseconds_in_day(self):
        t = time(15, 30, 12, 345000)
        fmt = dates.DateTimeFormat(t, locale='en_US')
        self.assertEqual('55812345', fmt['AAAA'])

    def test_milliseconds_in_day_zero(self):
        d = time(0, 0, 0)
        fmt = dates.DateTimeFormat(d, locale='en_US')
        self.assertEqual('0000', fmt['AAAA'])

    def test_timezone_rfc822(self):
        tz = timezone('Europe/Berlin')
        t = time(15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(t, locale='de_DE')
        self.assertEqual('+0100', fmt['Z'])

    def test_timezone_gmt(self):
        tz = timezone('Europe/Berlin')
        t = time(15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(t, locale='de_DE')
        self.assertEqual('GMT+01:00', fmt['ZZZZ'])

    def test_timezone_no_uncommon(self):
        tz = timezone('Europe/Paris')
        dt = datetime(2007, 4, 1, 15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(dt, locale='fr_CA')
        self.assertEqual('France', fmt['v'])

    def test_timezone_with_uncommon(self):
        tz = timezone('Europe/Paris')
        dt = datetime(2007, 4, 1, 15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(dt, locale='fr_CA')
        self.assertEqual('HEC', fmt['V'])

    def test_timezone_location_format(self):
        tz = timezone('Europe/Paris')
        dt = datetime(2007, 4, 1, 15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(dt, locale='fr_FR')
        self.assertEqual('France', fmt['VVVV'])

    def test_timezone_walltime_short(self):
        tz = timezone('Europe/Paris')
        t = time(15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(t, locale='fr_FR')
        self.assertEqual('HEC', fmt['v'])

    def test_timezone_walltime_long(self):
        tz = timezone('Europe/Paris')
        t = time(15, 30, tzinfo=tz)
        fmt = dates.DateTimeFormat(t, locale='fr_FR')
        self.assertEqual(u'heure d’Europe centrale', fmt['vvvv'])

    def test_hour_formatting(self):
        l = 'en_US'
        t = time(0, 0, 0)
        self.assertEqual(dates.format_time(t, 'h a', locale=l), '12 AM')
        self.assertEqual(dates.format_time(t, 'H', locale=l), '0')
        self.assertEqual(dates.format_time(t, 'k', locale=l), '24')
        self.assertEqual(dates.format_time(t, 'K a', locale=l), '0 AM')
        t = time(12, 0, 0)
        self.assertEqual(dates.format_time(t, 'h a', locale=l), '12 PM')
        self.assertEqual(dates.format_time(t, 'H', locale=l), '12')
        self.assertEqual(dates.format_time(t, 'k', locale=l), '12')
        self.assertEqual(dates.format_time(t, 'K a', locale=l), '0 PM')


class FormatDateTestCase(unittest.TestCase):

    def test_with_time_fields_in_pattern(self):
        self.assertRaises(AttributeError, dates.format_date, date(2007, 04, 01),
                          "yyyy-MM-dd HH:mm", locale='en_US')

    def test_with_time_fields_in_pattern_and_datetime_param(self):
        self.assertRaises(AttributeError, dates.format_date,
                          datetime(2007, 04, 01, 15, 30),
                          "yyyy-MM-dd HH:mm", locale='en_US')


class FormatTimeTestCase(unittest.TestCase):

    def test_with_naive_datetime_and_tzinfo(self):
        string = dates.format_time(datetime(2007, 4, 1, 15, 30),
                                   'long', tzinfo=timezone('US/Eastern'),
                                   locale='en')
        self.assertEqual('11:30:00 AM EDT', string)

    def test_with_date_fields_in_pattern(self):
        self.assertRaises(AttributeError, dates.format_time, date(2007, 04, 01),
                          "yyyy-MM-dd HH:mm", locale='en_US')

    def test_with_date_fields_in_pattern_and_datetime_param(self):
        self.assertRaises(AttributeError, dates.format_time,
                          datetime(2007, 04, 01, 15, 30),
                          "yyyy-MM-dd HH:mm", locale='en_US')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(dates))
    suite.addTest(unittest.makeSuite(DateTimeFormatTestCase))
    suite.addTest(unittest.makeSuite(FormatDateTestCase))
    suite.addTest(unittest.makeSuite(FormatTimeTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
