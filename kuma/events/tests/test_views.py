from nose.tools import eq_, ok_

from pyquery import PyQuery as pq
from waffle.models import Flag

from sumo.urlresolvers import reverse
from devmo.tests import KumaTestCase

from ..cron import calendar_reload


class EventsViewsTest(KumaTestCase):
    fixtures = ['calendar.json']

    def setUp(self):
        super(EventsViewsTest, self).setUp()
        calendar_reload()

    def test_events(self):
        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_events_map_flag(self):
        url = reverse('events')

        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_([], doc.find('#map_canvas'))
        ok_("maps.google.com" not in r.content)

        events_map_flag = Flag.objects.create(name='events_map', everyone=True)
        events_map_flag.save()

        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc.find('#map_canvas')))
        ok_("maps.google.com" in r.content)
