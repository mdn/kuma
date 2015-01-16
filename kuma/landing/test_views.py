from nose.tools import eq_, ok_

from kuma.core.tests import KumaTestCase
from kuma.core.urlresolvers import reverse


class LearnViewsTest(KumaTestCase):

    def test_learn(self):
        url = reverse('learn')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_html(self):
        url = reverse('learn_html')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_css(self):
        url = reverse('learn_css')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_javascript(self):
        url = reverse('learn_javascript')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)


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
