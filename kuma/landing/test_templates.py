from nose.tools import eq_, ok_

from constance.test import override_config

from kuma.core.urlresolvers import reverse
from kuma.core.tests import KumaTestCase


class HomeTests(KumaTestCase):
    def test_google_analytics(self):
        url = reverse('home')

        with override_config(GOOGLE_ANALYTICS_ACCOUNT='0'):
            r = self.client.get(url, follow=True)
            eq_(200, r.status_code)
            ok_('ga(\'create' not in r.content)

        with override_config(GOOGLE_ANALYTICS_ACCOUNT='UA-99999999-9'):
            r = self.client.get(url, follow=True)
            eq_(200, r.status_code)
            ok_('ga(\'create' in r.content)
