from django.test import RequestFactory

from kuma.core.tests import KumaTestCase, eq_

from ..context_processors import next_url


class TestNextUrl(KumaTestCase):
    """
    Tests that the next_url value is properly set,
    including query string
    """
    rf = RequestFactory()

    def test_basic(self):
        path = '/one/two'
        request = self.rf.get(path)
        eq_(next_url(request)['next_url'], path)

    def test_querystring(self):
        path = '/one/two?something'
        request = self.rf.get(path)
        eq_(next_url(request)['next_url'], path)
