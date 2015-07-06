from StringIO import StringIO

from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory

from nose.tools import eq_

from kuma.core.tests import KumaTestCase

from ..context_processors import next_url


def _make_request(path):
    req = WSGIRequest({
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': path,
        'wsgi.input': StringIO()})
    req.user = AnonymousUser()
    return req


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
