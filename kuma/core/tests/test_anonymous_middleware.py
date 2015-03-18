from nose.tools import eq_

from django.http import HttpResponse
from django.conf import settings
from django.test import RequestFactory

from kuma.core.tests import KumaTestCase

from ..anonymous import AnonymousIdentityMiddleware


class TestAnonymousMiddleware(KumaTestCase):
    """Tests for the anonymous middleware."""
    def setUp(self):
        super(TestAnonymousMiddleware, self).setUp()
        self.middleware = AnonymousIdentityMiddleware()
        self.rf = RequestFactory()

    def test_cookie_set(self):
        """The anonymous cookie is set when the anonymous id is created."""
        # Create and process a request
        request = self.rf.request()
        self.middleware.process_request(request)

        # Make sure anonymous id isn't set then access it to generate it
        eq_(False, request.anonymous.has_id)
        anon_id = request.anonymous.anonymous_id
        eq_(True, request.anonymous.has_id)

        # Create and process the response
        response = HttpResponse()
        response = self.middleware.process_response(request, response)

        # Make sure cookie is set with correct value
        eq_(True, settings.ANONYMOUS_COOKIE_NAME in response.cookies)
        eq_(anon_id, response.cookies[settings.ANONYMOUS_COOKIE_NAME].value)

    def test_cookie_not_set(self):
        """The anonymous cookie isn't set if it isn't created."""
        # Create and process a request
        request = self.rf.request()
        self.middleware.process_request(request)

        # Check if anonymous id is set (without creating one)
        request.anonymous.has_id

        # Create and process the response
        response = HttpResponse()
        response = self.middleware.process_response(request, response)

        # Make sure cookie was't set
        eq_(False, settings.ANONYMOUS_COOKIE_NAME in response.cookies)

    def test_cookie_exists(self):
        """Anonymous cookie is already set.
        Make sure the value is read correctly and a new one isn't set."""
        # Create, add the anonymous cookie and process a request
        request = self.rf.request()
        anon_id = '63de20c227be94560e3c679330c678ee'
        request.COOKIES[settings.ANONYMOUS_COOKIE_NAME] = anon_id
        self.middleware.process_request(request)

        # Make sure anonymous id is set to the right value
        eq_(True, request.anonymous.has_id)
        eq_(anon_id, request.anonymous.anonymous_id)

        # Create and process the response
        response = HttpResponse()
        response = self.middleware.process_response(request, response)

        # Make sure cookie was't set
        eq_(False, settings.ANONYMOUS_COOKIE_NAME in response.cookies)
