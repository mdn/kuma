import pytest
from django.conf import settings

from kuma.core.tests import assert_no_cache_header, assert_shared_cache_header
from kuma.core.urlresolvers import reverse

from . import ElasticTestCase
from ..models import Filter, FilterGroup, Index
from ..pagination import SearchPagination
from ..views import SearchView


class ViewTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ["wiki/documents.json", "search/filters.json"]

    def test_search_filters(self):
        response = self.client.get(
            "/en-US/search?q=article", HTTP_HOST=settings.WIKI_HOST
        )
        assert response.status_code == 200
        assert_no_cache_header(response)
        content = response.content.decode()
        assert "Results for" in content
        assert "an article title" in content
        assert '4 documents found for "article" in English' in content

    def test_serialized_filters(self):
        class Test1SearchView(SearchView):
            filter_backends = ()

            def dispatch(self, *args, **kwargs):
                super(Test1SearchView, self).dispatch(*args, **kwargs)
                assert len(self.serialized_filters) == 1
                serialized_filter = self.serialized_filters[0]
                assert serialized_filter["name"] == "Tagged"
                assert serialized_filter["slug"] == "tagged"
                assert serialized_filter["shortcut"] is None
                assert list(serialized_filter["tags"]) == ["tagged"]
                assert serialized_filter["operator"] == "OR"
                assert serialized_filter["group"] == {
                    "order": 1,
                    "name": "Group",
                    "slug": "group",
                }

        test_view1 = Test1SearchView.as_view()
        test_view1(self.get_request("/en-US/"))

        group = FilterGroup.objects.get(name="Group")
        Filter.objects.create(name="Serializer", slug="serializer", group=group)

        class Test2SearchView(SearchView):
            filter_backends = ()

            def dispatch(self, *args, **kwargs):
                super(Test2SearchView, self).dispatch(*args, **kwargs)
                assert len(self.serialized_filters) == 2
                filter_1, filter_2 = self.serialized_filters
                assert filter_1["name"] == "Tagged"
                assert filter_1["slug"] == "tagged"
                assert filter_1["shortcut"] is None
                assert list(filter_1["tags"]) == ["tagged"]
                assert filter_1["operator"] == "OR"
                assert filter_1["group"] == {
                    "order": 1,
                    "name": "Group",
                    "slug": "group",
                }
                assert filter_2["name"] == "Serializer"
                assert filter_2["slug"] == "serializer"
                assert filter_2["shortcut"] is None
                assert list(filter_2["tags"]) == []
                assert filter_2["operator"] == "OR"
                assert filter_2["group"] == {
                    "order": 1,
                    "name": "Group",
                    "slug": "group",
                }

        test_view2 = Test2SearchView.as_view()
        test_view2(self.get_request("/en-US/"))

    def test_filters(self):
        class FilterSearchView(SearchView):
            expected = None
            filter_backends = ()

            def dispatch(self, *args, **kwargs):
                super(FilterSearchView, self).dispatch(*args, **kwargs)
                assert list(self.selected_filters) == list(self.expected)

        view = FilterSearchView.as_view(expected=["spam"])
        view(self.get_request("/en-US/?group=spam"))

        # the filters are deduplicated
        view = FilterSearchView.as_view(expected=["spam", "eggs"])
        view(self.get_request("/en-US/?group=spam&group=eggs"))
        view(self.get_request("/en-US/?group=spam&group=eggs&group=spam"))

    def test_queryset(self):
        class QuerysetSearchView(SearchView):
            def list(self, *args, **kwargs):
                response = super(QuerysetSearchView, self).list(*args, **kwargs)
                data = response.data

                # queryset content
                docs = data["documents"]
                assert docs[0]["title"] == "an article title"
                assert docs[0]["locale"] == "en-US"

                # metadata
                assert self.current_page == 1
                assert len(self.serialized_filters) == 1
                assert list(self.selected_filters) == ["tagged"]
                assert self.url == self.request.get_full_path()

                # aggregations
                filters = data["filters"]
                assert len(filters) == 1
                assert filters[0]["name"] == "Group"
                assert filters[0]["options"][0]["name"] == "Tagged"
                assert filters[0]["options"][0]["count"] == 2
                assert filters[0]["options"][0]["active"]
                return response

        view = QuerysetSearchView.as_view()
        request = self.get_request("/en-US/search?q=article&group=tagged")
        view(request)

    def test_allowed_methods(self):
        response = self.client.get("/en-US/search?q=test")
        assert response.status_code == 200

        response = self.client.head("/en-US/search?q=test")
        assert response.status_code == 405
        assert_no_cache_header(response)

        response = self.client.post("/en-US/search?q=test")
        assert response.status_code == 405
        assert_no_cache_header(response)

    def test_paginate_by_param(self):
        request = self.get_request("/en-US/search")

        class TestPageNumberPagination(SearchPagination):
            page_size = 1
            page_size_query_param = "per_page"

        class PaginationSearchView(SearchView):
            pagination_class = TestPageNumberPagination

        view = PaginationSearchView.as_view()
        response = view(request)
        assert response.data["pages"] == 6

        request = self.get_request("/en-US/search?per_page=4")
        response = view(request)
        assert response.data["pages"] == 2

    def test_paginate_too_large(self):
        response = self.client.get(
            "/en-US/search", {"page": 1000}, HTTP_HOST=settings.WIKI_HOST
        )
        # It's a bit odd that an invalid query string parameter
        # causes a 404 Not Found but that's how the paginator for
        # rest_framework works.
        assert response.status_code == 404

    def test_page_too_large(self):
        # Note that this doesn't use the Wiki host
        response = self.client.get("/en-US/search", {"page": 2, "q": "anything"})
        # The search 'q' is fine and the page isn't too large on its own, but
        # the pagination doesn't go beyond the first page so the rest_frameworks
        # pagination will trigger an error.
        assert response.status_code == 400

    def test_tokenize_camelcase_titles(self):
        for q in ("get", "element", "by", "id"):
            response = self.client.get(
                "/en-US/search", {"q": q}, HTTP_HOST=settings.WIKI_HOST
            )
            assert response.status_code == 200
            assert b"camel-case-test" in response.content

    def test_index(self):
        self.client.login(username="admin", password="testpass")
        response = self.client.get("/en-US/search", HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        expected = f"Search index: {Index.objects.get_current().name}"
        assert expected in response.content.decode(response.charset)

    def test_api_redirect(self):
        response = self.client.get("/en-US/search.json", HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 301


@pytest.mark.parametrize("locale", ["en-US", "fr"])
def test_search_plugin(db, client, locale):
    response = client.get(reverse("search.plugin", locale=locale))
    assert response.status_code == 200
    assert_shared_cache_header(response)
    assert response["Content-Type"] == "application/opensearchdescription+xml"
    assert "search/plugin.html" in [t.name for t in response.templates]
    assert "/{}/search".format(locale) in response.content.decode()
