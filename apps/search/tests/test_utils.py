from __future__ import absolute_import
from nose.tools import eq_

from test_utils import TestCase

from search.utils import QueryURLObject


class URLTests(TestCase):

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

    def test_merge_query_param(self):
        original = 'http://example.com/?spam=eggs'
        url = QueryURLObject(original)

        eq_(url.merge_query_param('spam', 'eggs'), original)
        eq_(url.merge_query_param('spam', 'spam'), original + '&spam=spam')
