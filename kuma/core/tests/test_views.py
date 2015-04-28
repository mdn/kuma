from nose.tools import eq_
from pyquery import PyQuery as pq
from soapbox.models import Message

from django.conf import settings
from django.core import mail

from kuma.core.tests import KumaTestCase

from ..urlresolvers import reverse


class LoggingTests(KumaTestCase):
    urls = 'kuma.core.tests.logging_urls'

    def setUp(self):
        self.old_logging = settings.LOGGING

    def tearDown(self):
        settings.LOGGING = self.old_logging

    def test_no_mail_handler(self):
        try:
            response = self.client.get('/en-US/test_exception/')
            eq_(500, response.status_code)
            eq_(0, len(mail.outbox))
        except:
            pass

    def test_mail_handler(self):
        settings.LOGGING['loggers']['django.request'] = ['console', 'mail_admins']
        try:
            response = self.client.get('/en-US/test_exception/')
            eq_(500, response.status_code)
            eq_(1, len(mail.outbox))
        except:
            pass


class SoapboxViewsTest(KumaTestCase):
    fixtures = ['devmo_calendar.json']

    def test_global_home(self):
        m = Message(message="Global", is_global=True, is_active=True, url="/")
        m.save()

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

    def test_subsection(self):
        m = Message(message="Events", is_global=False, is_active=True,
                    url="/events/")
        m.save()

        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))

    def test_inactive(self):
        m = Message(message="Events", is_global=False, is_active=False,
                    url="/events/")
        m.save()

        url = reverse('events')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))
