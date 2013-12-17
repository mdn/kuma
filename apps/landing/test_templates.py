from nose.tools import eq_, ok_
import test_utils

from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse

from devmo.tests import override_constance_settings

class HomeTests(test_utils.TestCase):
    def setUp(self):
        self.client = LocalizingClient()

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
