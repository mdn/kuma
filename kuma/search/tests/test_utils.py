from kuma.core.tests import KumaTestCase
from kuma.core.utils import order_params

from ..utils import QueryURLObject


class URLTests(KumaTestCase):
    def test_pop_query_param(self):
        original = "http://example.com/?spam=eggs"
        url = QueryURLObject(original)

        assert "http://example.com/" == url.pop_query_param("spam", "eggs")
        assert original == url.pop_query_param("spam", "spam")

        original = "http://example.com/?spam=eggs&spam=spam"
        url = QueryURLObject(original)
        assert "http://example.com/?spam=spam" == url.pop_query_param("spam", "eggs")
        assert "http://example.com/?spam=eggs" == url.pop_query_param("spam", "spam")

        original = "http://example.com/?spam=eggs&foo="
        url = QueryURLObject(original)
        assert "http://example.com/?foo=" == url.pop_query_param("spam", "eggs")

    def test_merge_query_param(self):
        original = "http://example.com/?spam=eggs"
        url = QueryURLObject(original)

        assert original == url.merge_query_param("spam", "eggs")
        assert original + "&spam=spam" == url.merge_query_param("spam", "spam")

        original = "http://example.com/?foo=&spam=eggs&foo=bar"
        url = QueryURLObject(original)

        merged_url = order_params(url.merge_query_param("foo", None))
        assert merged_url == "http://example.com/?foo=&foo=bar&spam=eggs"

        merged_url = order_params(url.merge_query_param("foo", [None]))
        assert merged_url == "http://example.com/?foo=&foo=bar&spam=eggs"

        # bug 930300
        url = QueryURLObject(
            "http://example.com/en-US/search?q=javascript%20&&&highlight=false"
        )
        merged_url = order_params(url.merge_query_param("topic", "api"))
        assert (
            merged_url
            == "http://example.com/en-US/search?highlight=false&q=javascript&topic=api"
        )

    def test_clean_params(self):
        for url in ["http://example.com/?spam=", "http://example.com/?spam"]:
            url_object = QueryURLObject(url)
            assert not url_object.clean_params(url_object.query_dict)
