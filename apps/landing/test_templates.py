# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_, ok_
from pyquery import PyQuery as pq
import test_utils

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse

from devmo.tests import override_constance_settings

def get_promos(client, url, selector):
    r = client.get(url, follow=True)
    eq_(200, r.status_code)
    doc = pq(r.content)
    promo = doc.find(selector)
    return promo


class HomeTests(test_utils.TestCase):
    def setUp(self):
        self.client = LocalizingClient()

    def test_social_promo(self):
        url = reverse('landing.views.home')
        promo = get_promos(self.client, url, '#promo-fosdev')
        ok_(promo)

    def test_google_analytics(self):
        url = reverse('landing.views.home')

        with override_constance_settings(GOOGLE_ANALYTICS_ACCOUNT='0'):
            r = self.client.get(url, follow=True)
            eq_(200, r.status_code)
            ok_('var _gaq' not in r.content)

        with override_constance_settings(GOOGLE_ANALYTICS_ACCOUNT='UA-99999999-9'):
            r = self.client.get(url, follow=True)
            eq_(200, r.status_code)
            ok_('var _gaq' in r.content)
