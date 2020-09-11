from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from elasticsearch import Elasticsearch
from elasticsearch_dsl.serializer import serializer as es_dsl_serializer

from kuma.wiki.models import Document
from kuma.wiki.search import WikiDocumentType
from kuma.wiki.signals import render_done

from . import ElasticTestCase
from ..filters import (
    get_filters,
    HighlightFilterBackend,
    KeywordQueryBackend,
    LanguageFilterBackend,
    SearchQueryBackend,
    TagGroupFilterBackend,
)
from ..models import FilterGroup
from ..views import SearchView


class MockTransport(object):
    """
    A fake ElasticSearch transport object, avoiding network calls.

    Based on DummyTransport from elasticsearch:
    https://github.com/elastic/elasticsearch-py/blob/master/test_elasticsearch/test_cases.py
    """

    def __init__(self, hosts, responses=None, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
        self.responses = responses or []
        self.call_count = 0
        self.calls = []

    def perform_request(self, method, url, params=None, body=None):
        resp = 200, {}
        if self.responses:
            resp = self.responses[self.call_count]
        self.call_count += 1
        self.calls.append((method, url, params, body))
        return resp


@pytest.fixture
def mock_elasticsearch():
    """Create an Elasticsearch object that won't make network requests."""
    return Elasticsearch(transport_class=MockTransport, serializer=es_dsl_serializer)


@pytest.fixture
def mock_search(mock_elasticsearch):
    """Mock WikiDocumentType.search() for a fake Elasticsearch and index."""
    patcher_get_conn = mock.patch(
        "kuma.wiki.search.connections.get_connection", return_value=mock_elasticsearch
    )
    patcher_get_index = mock.patch(
        "kuma.wiki.search.WikiDocumentType.get_index", return_value="mdn-test"
    )
    patcher_get_conn.start()
    patcher_get_index.start()
    yield WikiDocumentType.search()
    patcher_get_index.stop()
    patcher_get_conn.stop()


# Testing version of named groups of tags for filtering
# This is serialized from the database in .views.SearchView.initial
FILTER_GROUP_GROUP = {"name": "Group", "slug": "group", "order": 1}
FILTER_GROUP_TOPIC = {"name": "Topics", "slug": "topic", "order": 1}
FILTER_GROUP_DOGS = {"name": "Dogs", "slug": "dogs", "order": 1}
SERIALIZED_FILTERS = [
    {
        # Test data from fixtures/search/filters.json
        "group": FILTER_GROUP_GROUP,
        "name": "Tagged",
        "operator": "OR",
        "shortcut": None,
        "slug": "tagged",
        "tags": ["tagged"],
    },
    {
        # Topic CSS
        "group": FILTER_GROUP_TOPIC,
        "name": "CSS",
        "operator": "OR",
        "shortcut": None,
        "slug": "css",
        "tags": ["CSS"],
    },
    {
        # Topic Add-ons & Extensions
        "group": FILTER_GROUP_TOPIC,
        "name": "Add-ons & Extensions",
        "operator": "OR",
        "shortcut": None,
        "slug": "addons",
        "tags": ["Add-ons", "Extensions"],
    },
    {
        # A FilterGroup with no tags (yet? to be deleted?)
        "group": FILTER_GROUP_DOGS,
        "name": "Bad Dogs",
        "operator": "OR",
        "shortcut": None,
        "slug": "baddogs",
        "tags": [],
    },
    {
        # A FilterGroup with an 'AND' combination of two terms
        # TODO: This isn't used in production, disallow AND
        "group": FILTER_GROUP_DOGS,
        "name": "Brown Dogs",
        "operator": "AND",
        "shortcut": None,
        "slug": "brown-dogs",
        "tags": ["Brown", "Dog"],
    },
]


def fake_view(request, selected_filters=None):
    """A fake django-rest-framework view with query_params."""
    view = mock.Mock()
    view.query_params = request.GET
    if selected_filters is not None:
        # TagGroupFilterBackend tests require these
        view.serialized_filters = SERIALIZED_FILTERS
        view.selected_filters = selected_filters
    return view


def test_base_search(db):
    """WikiDocumentType.search() searches all documents by default."""
    search = WikiDocumentType.search()
    assert search.to_dict() == {}


def test_base_search_mocked_es(mock_search):
    """Mocked WikiDocumentType.search() returns same search query."""
    assert mock_search.to_dict() == {}


def test_language_filter_backend_fr(rf, mock_search):
    """The LanguageFilterBackend gets en-US and fr docs, prefers fr."""
    backend = LanguageFilterBackend()
    request = rf.get("/fr/search?q=article")
    request.LANGUAGE_CODE = "fr"
    search = backend.filter_queryset(request, mock_search, None)
    expected = {
        "query": {
            "boosting": {
                "negative": {"bool": {"must_not": [{"term": {"locale": "fr"}}]}},
                "negative_boost": 0.5,
                "positive": {
                    "bool": {
                        "filter": [{"terms": {"locale": ["fr", "en-US"]}}],
                        "must": [{"match_all": {}}],
                    }
                },
            }
        }
    }
    assert search.to_dict() == expected


def test_language_filter_backend_en_US(rf, mock_search):
    """The LanguageFilterBackend can search for en-US-only docs."""
    backend = LanguageFilterBackend()
    request = rf.get("/en-US/search?q=article")
    request.LANGUAGE_CODE = "en-US"
    search = backend.filter_queryset(request, mock_search, None)
    expected = {
        "query": {
            "boosting": {
                "negative": {"bool": {"must_not": [{"term": {"locale": "en-US"}}]}},
                "negative_boost": 0.5,
                "positive": {
                    "bool": {
                        "filter": [{"terms": {"locale": ["en-US"]}}],
                        "must": [{"match_all": {}}],
                    }
                },
            }
        }
    }
    assert search.to_dict() == expected


def test_language_filter_backend_all(rf, mock_search):
    """The LanguageFilterBackend treats '*' as all locales."""
    backend = LanguageFilterBackend()
    request = rf.get("/en-US/search?q=article&locale=*")
    request.LANGUAGE_CODE = "en-US"
    search = backend.filter_queryset(request, mock_search, None)
    assert search.to_dict() == {}


def test_search_query_backend(rf, mock_search):
    """The SearchQueryBackend matches several fields against the query."""
    backend = SearchQueryBackend()
    request = rf.get("/en-US/search?q=article")
    request.user = AnonymousUser()
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    expected = {
        "query": {
            "function_score": {
                "functions": [{"field_value_factor": {"field": "boost"}}],
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"title": {"boost": 7.2, "query": "article"}}},
                            {"match": {"summary": {"boost": 2.0, "query": "article"}}},
                            {"match": {"content": {"boost": 1.0, "query": "article"}}},
                            {
                                "match_phrase": {
                                    "title": {"boost": 12.0, "query": "article"}
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {"boost": 8.0, "query": "article"}
                                }
                            },
                        ]
                    }
                },
            }
        }
    }
    assert search.to_dict() == expected


def test_search_query_backend_empty(rf, mock_search):
    """The SearchQueryBackend doesn't filter an empty query."""
    backend = SearchQueryBackend()
    request = rf.get("/en-US/search?q=")
    request.user = AnonymousUser()
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    assert search.to_dict() == {}


def test_search_query_backend_as_admin(rf, mock_search, admin_user):
    """The SearchQueryBackend adds explain=True for superusers."""
    backend = SearchQueryBackend()
    request = rf.get("/en-US/search?q=")
    request.user = admin_user
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    assert search.to_dict() == {"explain": True}


@pytest.mark.parametrize(
    "param",
    (
        "kumascript_macros",
        "css_classnames",
        "html_attributes",
    ),
)
def test_keyword_query(rf, mock_search, param):
    """The KeywordQueryBackend searches keywords."""
    backend = KeywordQueryBackend()
    request = rf.get("/en-US/search?%s=test" % param)
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    expected = {
        "query": {
            "bool": {"should": [{"term": {param: {"boost": 10.0, "value": "test"}}}]}
        }
    }
    assert search.to_dict() == expected


@pytest.mark.parametrize(
    "param",
    (
        "kumascript_macros",
        "css_classnames",
        "html_attributes",
    ),
)
def test_keyword_query_wildcard(rf, mock_search, param):
    """The KeywordQueryBackend can add wildcard searches."""
    backend = KeywordQueryBackend()
    request = rf.get("/en-US/search?%s=test*" % param)
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    expected = {
        "query": {
            "bool": {
                "should": [
                    {"term": {param: {"boost": 10.0, "value": "test"}}},
                    {"wildcard": {param: {"boost": 5.0, "value": "test*"}}},
                ]
            }
        }
    }
    assert search.to_dict() == expected


def test_keyword_query_ignores_unknown_index(rf, mock_search):
    """The KeywordQueryBackend ignores an unknown parameter."""
    backend = KeywordQueryBackend()
    request = rf.get("/en-US/search?topic=test")
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    assert search.to_dict() == {}


def test_tag_group_filter_backend(rf, mock_search):
    """The TagGroupFilterBackend filters and aggregates by groups of tags."""
    backend = TagGroupFilterBackend()
    request = rf.get("/en-US/search?group=tagged")
    view = fake_view(request, selected_filters=["tagged"])
    search = backend.filter_queryset(request, mock_search, view)
    expected = {
        "post_filter": {"term": {"tags": "tagged"}},
        "aggs": {
            "addons": {"filter": {"terms": {"tags": ["Add-ons", "Extensions"]}}},
            "css": {"filter": {"term": {"tags": "CSS"}}},
            "brown-dogs": {"filter": {"terms": {"tags": ["Brown", "Dog"]}}},
            "tagged": {"filter": {"term": {"tags": "tagged"}}},
        },
    }
    assert search.to_dict() == expected


def test_tag_group_filter_backend_multiple_tags_or_operator(rf, mock_search):
    """The TagGroupFilterBackend searches for any tag in an OR group."""
    backend = TagGroupFilterBackend()
    request = rf.get("/en-US/search?topic=addons")
    view = fake_view(request, selected_filters=["addons"])
    search = backend.filter_queryset(request, mock_search, view)
    expected = {
        "post_filter": {
            "bool": {
                "should": [
                    {"term": {"tags": "Add-ons"}},
                    {"term": {"tags": "Extensions"}},
                ]
            }
        },
        "aggs": {
            "addons": {"filter": {"terms": {"tags": ["Add-ons", "Extensions"]}}},
            "css": {"filter": {"term": {"tags": "CSS"}}},
            "brown-dogs": {"filter": {"terms": {"tags": ["Brown", "Dog"]}}},
            "tagged": {"filter": {"term": {"tags": "tagged"}}},
        },
    }
    assert search.to_dict() == expected


def test_tag_group_filter_backend_multiple_tags_and_operator(rf, mock_search):
    """The TagGroupFilterBackend searches for all tags in an AND group."""
    backend = TagGroupFilterBackend()
    request = rf.get("/en-US/search?dogs=brown-dogs")
    view = fake_view(request, selected_filters=["brown-dogs"])
    search = backend.filter_queryset(request, mock_search, view)
    expected = {
        "post_filter": {
            "bool": {"must": [{"term": {"tags": "Brown"}}, {"term": {"tags": "Dog"}}]}
        },
        "aggs": {
            "addons": {"filter": {"terms": {"tags": ["Add-ons", "Extensions"]}}},
            "css": {"filter": {"term": {"tags": "CSS"}}},
            "brown-dogs": {"filter": {"terms": {"tags": ["Brown", "Dog"]}}},
            "tagged": {"filter": {"term": {"tags": "tagged"}}},
        },
    }
    assert search.to_dict() == expected


def test_tag_group_filter_backend_multiple_groups(rf, mock_search):
    """The TagGroupFilterBackend searches for multiple groups."""
    backend = TagGroupFilterBackend()
    request = rf.get("/en-US/search?topic=addons,css")
    view = fake_view(request, selected_filters=["addons", "css"])
    search = backend.filter_queryset(request, mock_search, view)
    expected = {
        "post_filter": {
            "bool": {
                "should": [
                    {"term": {"tags": "CSS"}},
                    {"term": {"tags": "Add-ons"}},
                    {"term": {"tags": "Extensions"}},
                ]
            }
        },
        "aggs": {
            "addons": {"filter": {"terms": {"tags": ["Add-ons", "Extensions"]}}},
            "css": {"filter": {"term": {"tags": "CSS"}}},
            "brown-dogs": {"filter": {"terms": {"tags": ["Brown", "Dog"]}}},
            "tagged": {"filter": {"term": {"tags": "tagged"}}},
        },
    }
    assert search.to_dict() == expected


def test_tag_group_filter_backend_no_groups(rf, mock_search):
    """The TagGroupFilterBackend still counts if no groups are selected."""
    backend = TagGroupFilterBackend()
    request = rf.get("/en-US/search")
    view = fake_view(request, selected_filters=[])
    search = backend.filter_queryset(request, mock_search, view)
    expected = {
        "aggs": {
            "addons": {"filter": {"terms": {"tags": ["Add-ons", "Extensions"]}}},
            "css": {"filter": {"term": {"tags": "CSS"}}},
            "brown-dogs": {"filter": {"terms": {"tags": ["Brown", "Dog"]}}},
            "tagged": {"filter": {"term": {"tags": "tagged"}}},
        }
    }
    assert search.to_dict() == expected


def test_highlight_filter_backend(rf, mock_search):
    """The HighlightFilterBackend highlights with marks."""
    backend = HighlightFilterBackend()
    request = rf.get("/en-US/search?highlight=1")
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    expected = {
        "highlight": {
            "fields": {"content": {}, "summary": {}},
            "order": "score",
            "post_tags": ["</mark>"],
            "pre_tags": ["<mark>"],
        }
    }
    assert search.to_dict() == expected


def test_highlight_filter_backend_no_highlight(rf, mock_search):
    """The HighlightFilterBackend checks that highlight is selected."""
    backend = HighlightFilterBackend()
    request = rf.get("/en-US/search")
    search = backend.filter_queryset(request, mock_search, fake_view(request))
    assert search.to_dict() == {}


class FilterTexts(ElasticTestCase):
    """Filter tests that require a database and ES server."""

    fixtures = ElasticTestCase.fixtures + ["wiki/documents.json", "search/filters.json"]

    def test_search_query(self):
        class SearchQueryView(SearchView):
            filter_backends = (SearchQueryBackend,)

        view = SearchQueryView.as_view()
        request = self.get_request("/en-US/search?q=article")
        response = view(request)
        assert len(response.data["documents"]) == response.data["count"] == 4
        assert "CSS/article-title-3" == response.data["documents"][0]["slug"]
        assert "en-US" == response.data["documents"][0]["locale"]

    def test_keyword_query(self):
        """Test keyword query filter."""
        # Update a document so that it has a `css_classname` and trigger a
        # reindex via `render_done`.
        doc = Document.objects.get(pk=1)
        doc.rendered_html = '<html><body class="eval">foo()</body></html>'
        doc.save()
        render_done.send(sender=Document, instance=doc, invalidate_cdn_cache=False)
        self.refresh()

        class View(SearchView):
            filter_backends = (KeywordQueryBackend,)

        view = View.as_view()
        request = self.get_request("/en-US/search?css_classnames=eval")
        response = view(request)
        assert len(response.data["documents"]) == response.data["count"] == 1
        assert doc.slug == response.data["documents"][0]["slug"]
        assert doc.locale == response.data["documents"][0]["locale"]

    def test_highlight_filter(self):
        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request("/en-US/search?q=article")
        response = view(request)
        assert "<mark>article</mark>" in response.data["documents"][0]["excerpt"]

    def test_no_highlight_filter(self):
        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request("/en-US/search?q=article&highlight=false")
        response = view(request)
        assert "<mark>" not in response.data["documents"][0]["excerpt"]

    def test_language_filter(self):
        class LanguageView(SearchView):
            filter_backends = (LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request("/fr/search?q=article")
        assert "fr" == request.LANGUAGE_CODE
        response = view(request)

        assert len(response.data["documents"]) == response.data["count"] == 7
        assert "fr" == response.data["documents"][0]["locale"]

        request = self.get_request("/en-US/search?q=article")
        assert "en-US" == request.LANGUAGE_CODE
        response = view(request)
        assert len(response.data["documents"]) == response.data["count"] == 6
        assert "en-US" == response.data["documents"][0]["locale"]

    def test_language_filter_override(self):
        """Ensure locale override can find the only 'fr' document."""

        class LanguageView(SearchView):
            filter_backends = (
                SearchQueryBackend,
                LanguageFilterBackend,
            )

        view = LanguageView.as_view()
        request = self.get_request("/en-US/search?q=pipe&locale=*")
        assert "en-US" == request.LANGUAGE_CODE
        response = view(request)

        assert len(response.data["documents"]) == response.data["count"] == 1
        assert "fr" == response.data["documents"][0]["locale"]

        request = self.get_request("/en-US/search?q=pipe")
        assert "en-US" == request.LANGUAGE_CODE
        response = view(request)
        assert len(response.data["documents"]) == response.data["count"] == 0

    def test_tag_group_filter(self):
        class TagGroupFilterView(SearchView):
            filter_backends = (TagGroupFilterBackend,)

        view = TagGroupFilterView.as_view()
        request = self.get_request("/en-US/search?group=tagged")
        response = view(request)
        assert len(response.data["documents"]) == response.data["count"] == 2
        assert "article-title" == response.data["documents"][0]["slug"]
        assert [
            {
                "name": "Group",
                "slug": "group",
                "options": [
                    {
                        "name": "Tagged",
                        "slug": "tagged",
                        "count": 2,
                        "active": True,
                        "urls": {
                            "active": "/en-US/search?group=tagged",
                            "inactive": "/en-US/search",
                        },
                    }
                ],
            },
        ] == response.data["filters"]

        request = self.get_request("/fr/search?group=non-existent")
        response = view(request)
        assert len(response.data["documents"]) == response.data["count"] == 7

    def test_get_filters(self):
        FilterGroup.objects.create(name="Topics", slug="topic", order=1)
        qd = QueryDict("q=test&topic=css,canvas,js")
        filters = get_filters(qd.getlist)
        assert ["css,canvas,js"] == list(filters)

        qd = QueryDict("q=test&topic=css,js&none=none")
        filters = get_filters(qd.getlist)
        assert ["none"] == filters

        qd = QueryDict("q=test&none=none")
        filters = get_filters(qd.getlist)
        assert ["none"] == filters
