import os
import csv

from nose.tools import ok_, eq_

from kuma.core.tests import KumaTestCase

from ..models import Event, Calendar

fixtures = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixtures')
MOZILLA_PEOPLE_EVENTS_CSV = os.path.join(fixtures, 'Mozillapeopleevents.csv')
XSS_CSV = os.path.join(fixtures, 'xss.csv')
BAD_DATE_CSV = os.path.join(fixtures, 'bad_date.csv')


class TestCalendar(KumaTestCase):
    fixtures = ['calendar.json']

    def setUp(self):
        self.cal = Calendar.objects.get(shortname='devengage_events')
        self.event = Event(date="2011-06-17", conference="Web2Day",
                           location="Nantes, France",
                           people="Christian Heilmann",
                           description="TBD", done="no", calendar=self.cal)
        self.event.save()

    def test_reload_bad_url_does_not_delete_data(self):
        self.cal.url = 'bad'
        success = self.cal.reload()
        ok_(not success)
        ok_(Event.objects.all()[0].conference == 'Web2Day')
        self.cal.url = 'http://test/testcalspreadsheet'
        success = self.cal.reload()
        ok_(not success)
        ok_(Event.objects.all()[0].conference == 'Web2Day')

    def test_reload_from_csv_data(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # check total
        eq_(33, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_reload_from_csv_data_blank_end_date(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        event = Event.objects.get(conference='Monash University')
        ok_(event)
        eq_(event.date, event.end_date)

    def test_reload_end_date_determines_done(self):
        self.cal.reload(data=csv.reader(open(MOZILLA_PEOPLE_EVENTS_CSV, 'rb')))
        # no matter what done column says, events should be done
        # by virtue of the end date
        event = Event.objects.get(conference='Confoo')
        ok_(event)
        eq_(True, event.done)
        event = Event.objects.get(conference='TECH4AFRICA')
        ok_(event)
        eq_(False, event.done)

    def test_bad_date_column_skips_row(self):
        self.cal.reload(data=csv.reader(open(BAD_DATE_CSV, 'rb')))
        # check total - should still have the good row
        eq_(1, len(Event.objects.all()))
        # spot-check
        ok_(Event.objects.get(conference='StarTechConf'))

    def test_html_santiziation(self):
        self.cal.reload(data=csv.reader(open(XSS_CSV, 'rb')))
        # spot-check
        eq_('&lt;script&gt;alert("ruh-roh");&lt;/script&gt;Brendan Eich',
            Event.objects.get(conference="Texas JavaScript").people)
