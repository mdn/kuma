from nose.tools import eq_, ok_

from sumo.urlresolvers import reverse
from devmo.tests import KumaTestCase, override_constance_settings


class HomeTests(KumaTestCase):
    def test_google_analytics(self):
        url = reverse('landing.views.home')

        with override_constance_settings(GOOGLE_ANALYTICS_ACCOUNT='0'):
            r = self.client.get(url, follow=True)
            eq_(200, r.status_code)
            ok_('ga(\'create' not in r.content)

        with override_constance_settings(GOOGLE_ANALYTICS_ACCOUNT='UA-99999999-9'):
            r = self.client.get(url, follow=True)
            eq_(200, r.status_code)
            ok_('ga(\'create' in r.content)
