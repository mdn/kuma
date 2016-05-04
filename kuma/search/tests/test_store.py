from __future__ import absolute_import

from django.contrib.sites.models import Site

import mock

from kuma.core.tests import KumaTestCase
from ..store import get_search_url_from_referer


class RefererTests(KumaTestCase):
    def generate_request(self, locale, referer):
        class _TestRequest(object):
            # In order to test this we just need an object that has
            # 'locale' and 'META', but not the full attribute set of
            # an HttpRequest. This is that object.
            def __init__(self, locale, referer):
                self.locale = locale
                self.META = {'HTTP_REFERER': referer}
                self.LANGUAGE_CODE = locale
        return _TestRequest(locale, referer)

    @mock.patch.object(Site.objects, 'get_current')
    def test_basic(self, get_current):
        get_current.return_value.domain = 'testserver'

        url = 'https://testserver/en-US/search?q=javascript'
        request = self.generate_request('en-US', url)
        assert get_search_url_from_referer(request) == url

    @mock.patch.object(Site.objects, 'get_current')
    def test_basic_with_topics(self, get_current):
        get_current.return_value.domain = 'testserver'

        url = 'https://testserver/en-US/search?q=javascript&topic=js'
        request = self.generate_request('en-US', url)
        assert get_search_url_from_referer(request) == url

    # FIXME: These tests aren't great because we can't verify exactly why we
    # got a None so we can't distinguish between "right answer" and "right
    # answer, but for the wrong reasons".

    @mock.patch.object(Site.objects, 'get_current')
    def test_bad_scheme(self, get_current):
        get_current.return_value.domain = 'testserver'

        url = 'http://testserver/en-US/search?q=javascript'
        request = self.generate_request('en-US', url)
        assert get_search_url_from_referer(request) is None

    @mock.patch.object(Site.objects, 'get_current')
    def test_bad_host(self, get_current):
        get_current.return_value.domain = 'testserver'

        url = 'https://evil.com/en-US/search?q=javascript'
        request = self.generate_request('en-US', url)
        assert get_search_url_from_referer(request) is None

    @mock.patch.object(Site.objects, 'get_current')
    def test_bad_path(self, get_current):
        get_current.return_value.domain = 'testserver'

        url = 'https://testserver/en-US/foo'
        request = self.generate_request('en-US', url)
        assert get_search_url_from_referer(request) is None

    @mock.patch.object(Site.objects, 'get_current')
    def test_referer_bad_encoding(self, get_current):
        get_current.return_value.domain = 'testserver'

        url = 'https://testserver/es/docs/Tutorial_de_XUL/A\xc3\x83\xc2\xb1adiendo_botones'
        request = self.generate_request('es', url)
        assert get_search_url_from_referer(request) is None
