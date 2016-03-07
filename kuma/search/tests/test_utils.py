from __future__ import absolute_import

from kuma.core.tests import KumaTestCase, eq_

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

        # bug 930300
        url = QueryURLObject('http://example.com/en-US/search?q=javascript%20&&&highlight=false')
        eq_(url.merge_query_param('topic', 'api'),
            'http://example.com/en-US/search?q=javascript&topic=api&highlight=false')

    def test_clean_params(self):
        for url in ['http://example.com/?spam=',
                    'http://example.com/?spam']:
            url_object = QueryURLObject(url)
            eq_(url_object.clean_params(url_object.query_dict), {})
