from nose.tools import eq_

from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class FlagitTestPermissions(TestCase):
    fixtures = ['users.json']

    def test_permission_required(self):
        """Test our new permission required decorator."""
        url = reverse('flagit.queue', force_locale=True)
        self.client.logout()
        resp = self.client.get(url)
        eq_(302, resp.status_code)

        self.client.login(username='tagger', password='testpass')
        resp = self.client.get(url)
        eq_(403, resp.status_code)

        self.client.login(username='admin', password='testpass')
        resp = self.client.get(url)
        eq_(200, resp.status_code)
