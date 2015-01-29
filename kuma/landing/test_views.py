from nose.tools import eq_, ok_

from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse


class LandingViewsTest(KumaTestCase):
    fixtures = ['test_data.json']

    def test_home(self):
        url = reverse('home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_promote_buttons(self):
        url = reverse('promote_buttons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_contribute_json(self):
        r = self.client.get(reverse('contribute_json'))
        eq_(200, r.status_code)
        ok_('application/json' in r['Content-Type'])
