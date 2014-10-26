from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.test import RequestFactory

import test_utils
from nose.tools import eq_

from sumo.urlresolvers import reverse
from sumo.views import redirect_to


class RedirectToTestcase(test_utils.TestCase):
    rf = RequestFactory()

    def test_redirect_to(self):
        resp = redirect_to(self.rf.get('/'), url='home', permanent=False)
        assert isinstance(resp, HttpResponseRedirect)
        eq_(reverse('home'), resp['location'])

    def test_redirect_permanent(self):
        resp = redirect_to(self.rf.get('/'), url='home')
        assert isinstance(resp, HttpResponsePermanentRedirect)
        eq_(reverse('home'), resp['location'])
