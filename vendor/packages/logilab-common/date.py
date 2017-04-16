# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""Date manipulation helper functions.




"""
__docformat__ = "restructuredtext en"

import math
from locale import getpreferredencoding
from datetime import date, time, datetime, timedelta
from time import strptime as time_strptime
from calendar import monthrange, timegm

try:
    from mx.DateTime import RelativeDateTime, Date, DateTimeType
except ImportError:
    from warnings import warn
    warn("mxDateTime not found, endOfMonth won't be available")
    endOfMonth = None
    DateTimeType = datetime
else:
    endOfMonth = RelativeDateTime(months=1, day=-1)

# NOTE: should we implement a compatibility layer between date representations
#       as we have in lgc.db ?

FRENCH_FIXED_HOLIDAYS = {
    'jour_an'        : '%s-01-01',
    'fete_travail'   : '%s-05-01',
    'armistice1945'  : '%s-05-08',
    'fete_nat'       : '%s-07-14',
    'assomption'     : '%s-08-15',
    'toussaint'      : '%s-11-01',
    'armistice1918'  : '%s-11-11',
    'noel'           : '%s-12-25',
    }

FRENCH_MOBILE_HOLIDAYS = {
    'paques2004'    : '2004-04-12',
    'ascension2004' : '2004-05-20',
    'pentecote2004' : '2004-05-31',

    'paques2005'    : '2005-03-28',
    'ascension2005' : '2005-05-05',
    'pentecote2005' : '2005-05-16',

    'paques2006'    : '2006-04-17',
    'ascension2006' : '2006-05-25',
    'pentecote2006' : '2006-06-05',

    'paques2007'    : '2007-04-09',
    'ascension2007' : '2007-05-17',
    'pentecote2007' : '2007-05-28',

    'paques2008'    : '2008-03-24',
    'ascension2008' : '2008-05-01',
    'pentecote2008' : '2008-05-12',

    'paques2009'    : '2009-04-13',
    'ascension2009' : '2009-05-21',
    'pentecote2009' : '2009-06-01',

    'paques2010'    : '2010-04-05',
    'ascension2010' : '2010-05-13',
    'pentecote2010' : '2010-05-24',

    'paques2011'    : '2011-04-25',
    'ascension2011' : '2011-06-02',
    'pentecote2011' : '2011-06-13',

    'paques2012'    : '2012-04-09',
    'ascension2012' : '2012-05-17',
    'pentecote2012' : '2012-05-28',
    }

# XXX this implementation cries for multimethod dispatching

def get_step(dateobj, nbdays=1):
    # assume date is either a python datetime or a mx.DateTime object
    if isinstance(dateobj, date):
        return ONEDAY * nbdays
    return nbdays # mx.DateTime is ok with integers

def datefactory(year, month, day, sampledate):
    # assume date is either a python datetime or a mx.DateTime object
    if isinstance(sampledate, datetime):
        return datetime(year, month, day)
    if isinstance(sampledate, date):
        return date(year, month, day)
    return Date(year, month, day)

def weekday(dateobj):
    # assume date is either a python datetime or a mx.DateTime object
    if isinstance(dateobj, date):
        return dateobj.weekday()
    return dateobj.day_of_week

def str2date(datestr, sampledate):
    # NOTE: datetime.strptime is not an option until we drop py2.4 compat
    year, month, day = [int(chunk) for chunk in datestr.split('-')]
    return datefactory(year, month, day, sampledate)

def days_between(start, end):
    if isinstance(start, date):
        delta = end - start
        # datetime.timedelta.days is always an integer (floored)
        if delta.seconds:
            return delta.days + 1
        return delta.days
    else:
        return int(math.ceil((end - start).days))

def get_national_holidays(begin, end):
    """return french national days off between begin and end"""
    begin = datefactory(begin.year, begin.month, begin.day, begin)
    end = datefactory(end.year, end.month, end.day, end)
    holidays = [str2date(datestr, begin)
                for datestr in FRENCH_MOBILE_HOLIDAYS.values()]
    for year in xrange(begin.year, end.year+1):
        for datestr in FRENCH_FIXED_HOLIDAYS.values():
            date = str2date(datestr % year, begin)
            if date not in holidays:
                holidays.append(date)
    return [day for day in holidays if begin <= day < end]

def add_days_worked(start, days):
    """adds date but try to only take days worked into account"""
    step = get_step(start)
    weeks, plus = divmod(days, 5)
    end = start + ((weeks * 7) + plus) * step
    if weekday(end) >= 5: # saturday or sunday
        end += (2 * step)
    end += len([x for x in get_national_holidays(start, end + step)
                if weekday(x) < 5]) * step
    if weekday(end) >= 5: # saturday or sunday
        end += (2 * step)
    return end

def nb_open_days(start, end):
    assert start <= end
    step = get_step(start)
    days = days_between(start, end)
    weeks, plus = divmod(days, 7)
    if weekday(start) > weekday(end):
        plus -= 2
    elif weekday(end) == 6:
        plus -= 1
    open_days = weeks * 5 + plus
    nb_week_holidays = len([x for x in get_national_holidays(start, end+step)
                            if weekday(x) < 5 and x < end])
    open_days -= nb_week_holidays
    if open_days < 0:
        return 0
    return open_days

def date_range(begin, end, incday=None, incmonth=None):
    """yields each date between begin and end

    :param begin: the start date
    :param end: the end date
    :param incr: the step to use to iterate over dates. Default is
                 one day.
    :param include: None (means no exclusion) or a function taking a
                    date as parameter, and returning True if the date
                    should be included.

    When using mx datetime, you should *NOT* use incmonth argument, use instead
    oneDay, oneHour, oneMinute, oneSecond, oneWeek or endOfMonth (to enumerate
    months) as `incday` argument
    """
    assert not (incday and incmonth)
    begin = todate(begin)
    end = todate(end)
    if incmonth:
        while begin < end:
            begin = next_month(begin, incmonth)
            yield begin
    else:
        incr = get_step(begin, incday or 1)
        while begin < end:
           yield begin
           begin += incr

# makes py datetime usable #####################################################

ONEDAY = timedelta(days=1)
ONEWEEK = timedelta(days=7)

try:
    strptime = datetime.strptime
except AttributeError: # py < 2.5
    from time import strptime as time_strptime
    def strptime(value, format):
        return datetime(*time_strptime(value, format)[:6])

def strptime_time(value, format='%H:%M'):
    return time(*time_strptime(value, format)[3:6])

def todate(somedate):
    """return a date from a date (leaving unchanged) or a datetime"""
    if isinstance(somedate, datetime):
        return date(somedate.year, somedate.month, somedate.day)
    assert isinstance(somedate, (date, DateTimeType)), repr(somedate)
    return somedate

def totime(somedate):
    """return a time from a time (leaving unchanged), date or datetime"""
    # XXX mx compat
    if not isinstance(somedate, time):
        return time(somedate.hour, somedate.minute, somedate.second)
    assert isinstance(somedate, (time)), repr(somedate)
    return somedate

def todatetime(somedate):
    """return a date from a date (leaving unchanged) or a datetime"""
    # take care, datetime is a subclass of date
    if isinstance(somedate, datetime):
        return somedate
    assert isinstance(somedate, (date, DateTimeType)), repr(somedate)
    return datetime(somedate.year, somedate.month, somedate.day)

def datetime2ticks(somedate):
    return timegm(somedate.timetuple()) * 1000

def days_in_month(somedate):
    return monthrange(somedate.year, somedate.month)[1]

def days_in_year(somedate):
    feb = date(somedate.year, 2, 1)
    if days_in_month(feb) == 29:
        return 366
    else:
        return 365

def previous_month(somedate, nbmonth=1):
    while nbmonth:
        somedate = first_day(somedate) - ONEDAY
        nbmonth -= 1
    return somedate

def next_month(somedate, nbmonth=1):
    while nbmonth:
        somedate = last_day(somedate) + ONEDAY
        nbmonth -= 1
    return somedate

def first_day(somedate):
    return date(somedate.year, somedate.month, 1)

def last_day(somedate):
    return date(somedate.year, somedate.month, days_in_month(somedate))

def ustrftime(somedate, fmt='%Y-%m-%d'):
    """like strftime, but returns a unicode string instead of an encoded
    string which' may be problematic with localized date.

    encoding is guessed by locale.getpreferredencoding()
    """
    # date format may depend on the locale
    encoding = getpreferredencoding(do_setlocale=False) or 'UTF-8'
    return unicode(somedate.strftime(str(fmt)), encoding)
