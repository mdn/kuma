from nose.tools import eq_
from django.test import RequestFactory

from kuma.core.tests import KumaTestCase
from ..middleware import SetRemoteAddrFromForwardedFor


class TrailingSlashMiddlewareTestCase(KumaTestCase):
    def test_no_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez')
        eq_(response.status_code, 404)

    def test_404_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez/')
        eq_(response.status_code, 404)

    def test_remove_trailing_slash(self):
        response = self.client.get(u'/en-US/docs/files/?xxx=\xc3')
        eq_(response.status_code, 301)
        assert response['Location'].endswith('/en-US/docs/files?xxx=%C3%83')


class SetRemoteAddrFromForwardedForTestCase(KumaTestCase):

    def test_rate_x_forwarded_for(self):
        rf = RequestFactory()
        middleware = SetRemoteAddrFromForwardedFor()

        req1 = rf.get('/', HTTP_X_FORWARDED_FOR='1.1.1.1')
        middleware.process_request(req1)
        eq_(req1.META['REMOTE_ADDR'], '1.1.1.1')

        req2 = rf.get('/', HTTP_X_FORWARDED_FOR='2.2.2.2')
        middleware.process_request(req2)
        eq_(req2.META['REMOTE_ADDR'], '2.2.2.2')

        req3 = rf.get('/', HTTP_X_FORWARDED_FOR='3.3.3.3, 4.4.4.4')
        middleware.process_request(req3)
        eq_(req3.META['REMOTE_ADDR'], '3.3.3.3')
