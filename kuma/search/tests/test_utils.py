from __future__ import absolute_import
from nose.tools import eq_, ok_

from kuma.core.tests import KumaTestCase

from ..store import referrer_url
from ..utils import QueryURLObject


class URLTests(KumaTestCase):

    def test_pop_query_param(self):
        original = 'http://example.com/?spam=eggs'
        url = QueryURLObject(original)

        eq_(url.pop_query_param('spam', 'eggs'), 'http://example.com/')
        eq_(url.pop_query_param('spam', 'spam'), original)

        original = 'http://example.com/?spam=eggs&spam=spam'
        url = QueryURLObject(original)
        eq_(url.pop_query_param('spam', 'eggs'),
            'http://example.com/?spam=spam')
        eq_(url.pop_query_param('spam', 'spam'),
            'http://example.com/?spam=eggs')

        original = 'http://example.com/?spam=eggs&foo='
        url = QueryURLObject(original)
        eq_(url.pop_query_param('spam', 'eggs'),
            'http://example.com/?foo=')

    def test_merge_query_param(self):
        original = 'http://example.com/?spam=eggs'
        url = QueryURLObject(original)

        eq_(url.merge_query_param('spam', 'eggs'), original)
        eq_(url.merge_query_param('spam', 'spam'), original + '&spam=spam')

        original = 'http://example.com/?foo=&spam=eggs&foo=bar'
        url = QueryURLObject(original)

        eq_(url.merge_query_param('foo', None),
            'http://example.com/?foo=&foo=bar&spam=eggs')

        eq_(url.merge_query_param('foo', [None]),
            'http://example.com/?foo=&foo=bar&spam=eggs')

    def test_clean_params(self):
        for url in ['http://example.com/?spam=',
                    'http://example.com/?spam']:
            url_object = QueryURLObject(url)
            eq_(url_object.clean_params(url_object.query_dict), {})

    def test_referer_bad_encoding(self):
        class _TestRequest(object):
            # In order to test this we just need an object that has
            # 'locale' and 'META', but not the full attribute set of
            # an HttpRequest. This is that object.
            def __init__(self, locale, referer):
                self.locale = locale
                self.META = {'HTTP_REFERER': referer}

        request = _TestRequest('es', 'http://developer.mozilla.org/es/docs/Tutorial_de_XUL/A\xc3\x83\xc2\xb1adiendo_botones')
        ok_(referrer_url(request) is None)
