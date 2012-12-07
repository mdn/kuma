from nose.tools import eq_, ok_
from pyquery import PyQuery as pq
import test_utils
from waffle.models import Switch
import constance.config

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse


def get_promos(client, url):
    r = client.get(url, follow=True)
    eq_(200, r.status_code)
    doc = pq(r.content)
    aurora_promo = doc.find('#promo-aurora')
    social_promo = doc.find('#promo-social')
    return aurora_promo, social_promo


class HomeTests(test_utils.TestCase):
    def setUp(self):
        self.client = LocalizingClient()

    def test_social_promo(self):
        url = reverse('landing.views.home')

        aurora_promo, social_promo = get_promos(self.client, url)
        ok_(aurora_promo)
        ok_(not social_promo)

        Switch.objects.create(name="social_promo", active=True)

        aurora_promo, social_promo = get_promos(self.client, url)
        ok_(not aurora_promo)
        ok_(social_promo)

    def test_google_analytics(self):
        url = reverse('landing.views.home')

        constance.config.GOOGLE_ANALYTICS_ACCOUNT = ''
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        ok_('var _gaq' not in r.content)

        constance.config.GOOGLE_ANALYTICS_ACCOUNT = 'UA-99999999-9'
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        ok_('var _gaq' in r.content)
