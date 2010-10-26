from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

from nose.tools import eq_
from test_utils import RequestFactory

from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from sumo.views import redirect_to


class RedirectToTestcase(TestCase):

    rf = RequestFactory()

    def test_redirect_to(self):
        resp = redirect_to(self.rf.get('/'), url='home', permanent=False)
        assert isinstance(resp, HttpResponseRedirect)
        eq_(reverse('home'), resp['location'])

    def test_redirect_permanent(self):
        resp = redirect_to(self.rf.get('/'), url='home')
        assert isinstance(resp, HttpResponsePermanentRedirect)
        eq_(reverse('home'), resp['location'])
