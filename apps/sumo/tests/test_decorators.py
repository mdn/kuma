from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse

from nose.tools import eq_
from test_utils import RequestFactory

from sumo.decorators import logout_required
from sumo.tests import TestCase


def simple_view(request):
    return HttpResponse()


class LogoutRequiredTestCase(TestCase):
    fixtures = ['users.json']

    def test_logged_out_default(self):
        request = RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = logout_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_default(self):
        request = RequestFactory().get('/foo')
        request.user = User.objects.get(username='jsocol')
        view = logout_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_argument(self):
        request = RequestFactory().get('/foo')
        request.user = User.objects.get(username='jsocol')
        view = logout_required('/bar')(simple_view)
        response = view(request)
        eq_(302, response.status_code)
        eq_('/bar', response['location'])
