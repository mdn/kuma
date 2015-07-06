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

    def test_global_home(self):
        m = Message(message="Global", is_global=True, is_active=True, url="/")
        m.save()

        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

        url = reverse('demos')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(m.message, doc.find('div.global-notice').text())

    def test_subsection(self):
        m = Message(message="Demos", is_global=False, is_active=True,
                    url="/demos/")
        m.save()

        url = reverse('demos')
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
        m = Message(message="Demos", is_global=False, is_active=False,
                    url="/demos/")
        m.save()

        url = reverse('demos')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_([], doc.find('div.global-notice'))


class EventsRedirectTest(KumaTestCase):

    def test_redirect_to_mozilla_org(self):
        url = '/en-US/events'
        response = self.client.get(url)
        eq_(302, response.status_code)
        eq_('https://mozilla.org/contribute/events', response['Location'])
