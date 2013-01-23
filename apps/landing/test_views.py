from nose.tools import eq_, ok_
from nose.plugins.skip import SkipTest
from mock import patch
from pyquery import PyQuery as pq
import test_utils
from waffle.models import Switch

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse


class LearnViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    def test_learn(self):
        url = reverse('landing.views.learn')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_html(self):
        url = reverse('landing.views.learn_html')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_html5(self):
        url = reverse('landing.views.learn_html5')
        r = self.client.get(url, follow=True)
        eq_(404, r.status_code)
        s = Switch.objects.create(name='html5_landing', active=True)
        s.save()
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        s.delete()

    def test_learn_css(self):
        url = reverse('landing.views.learn_css')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_learn_javascript(self):
        url = reverse('landing.views.learn_javascript')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)


class LandingViewsTest(test_utils.TestCase):
    fixtures = ['test_data.json', ]

    def setUp(self):
        self.client = LocalizingClient()

    def test_home(self):
        url = reverse('landing.views.home')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        dev_mdc_link = doc.find('a#dev-mdc-link')
        ok_(dev_mdc_link)

    def test_addons(self):
        url = reverse('landing.views.addons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_mozilla(self):
        url = reverse('landing.views.mozilla')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_mobile(self):
        url = reverse('landing.views.mobile')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_web(self):
        url = reverse('landing.views.web')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_search(self):
        raise SkipTest('Search test disabled until we switch to kuma wiki')
        url = reverse('landing.views.search')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

    def test_promote_buttons(self):
        url = reverse('landing.views.promote_buttons')
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)


class AppsViewsTest(test_utils.TestCase):

    def setUp(self):
        self.client = LocalizingClient()

    @patch('landing.views.basket.subscribe')
    def test_apps_subscription(self, subscribe):
        subscribe.return_value = True
        url = reverse('landing.views.apps_newsletter')

        r = self.client.post(url,
                {'format': 'html',
                 'email': 'testuser@test.com',
                 'agree': 'checked'},
            follow=True)
        eq_(200, r.status_code)
        # assert thank you message
        self.assertContains(r, 'Thank you')
        eq_(1, subscribe.call_count)

    @patch('landing.views.basket.subscribe')
    def test_apps_subscription_bad_values(self, subscribe):
        subscribe.return_value = True
        url = reverse('landing.views.apps_newsletter')
        r = self.client.post(url, {'format': 1, 'email': 'nope'})
        eq_(200, r.status_code)
        # assert error
        self.assertContains(r, 'Enter a valid e-mail address.')
        self.assertContains(r, 'Select a valid choice.')
        self.assertContains(r, 'You must agree to the privacy policy.')
