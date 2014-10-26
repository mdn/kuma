from nose.tools import eq_, ok_
import test_utils

from django.http import HttpResponse
from django.test import RequestFactory

from devmo.decorators import never_cache


def simple_view(request):
    return HttpResponse()


class TestNeverCache(test_utils.TestCase):

    def test_never_cache(self):
        request = RequestFactory().get('/foo')
        view = never_cache(simple_view)
        response = view(request)
        eq_(200, response.status_code)
        [ok_(value in response['Cache-Control'])
         for value in ['no-cache', 'no-store', 'must-revalidate']]
        ok_('no-cache' in response['Pragma'])
        eq_('0', response['Expires'])
