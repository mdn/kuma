from django.http import QueryDict

from kuma.wiki.models import Document
from kuma.wiki.signals import render_done

from . import ElasticTestCase
from ..filters import (AdvancedSearchQueryBackend, DatabaseFilterBackend,
                       get_filters, HighlightFilterBackend,
                       LanguageFilterBackend, SearchQueryBackend)
from ..models import FilterGroup
from ..views import SearchView


class FilterTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ['wiki/documents.json',
                                           'search/filters.json']

    def test_search_query(self):
        class SearchQueryView(SearchView):
            filter_backends = (SearchQueryBackend,)

        view = SearchQueryView.as_view()
        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        assert len(response.data['documents']) == response.data['count'] == 4
        assert 'CSS/article-title-3' == response.data['documents'][0]['slug']
        assert 'en-US' == response.data['documents'][0]['locale']

    def test_advanced_search_query(self):
        """Test advanced search query filter."""
        # Update a document so that it has a `css_classname` and trigger a
        # reindex via `render_done`.
        doc = Document.objects.get(pk=1)
        doc.rendered_html = '<html><body class="eval">foo()</body></html>'
        doc.save()
        render_done.send(sender=Document, instance=doc)
        self.refresh()

        class View(SearchView):
            filter_backends = (AdvancedSearchQueryBackend,)

        view = View.as_view()
        request = self.get_request('/en-US/search?css_classnames=eval')
        response = view(request)
        assert len(response.data['documents']) == response.data['count'] == 1
        assert doc.slug == response.data['documents'][0]['slug']
        assert doc.locale == response.data['documents'][0]['locale']

    def test_highlight_filter(self):
        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        assert '<mark>article</mark>' in response.data['documents'][0]['excerpt']

    def test_no_highlight_filter(self):
        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request('/en-US/search?q=article&highlight=false')
        response = view(request)
        assert '<mark>' not in response.data['documents'][0]['excerpt']

    def test_language_filter(self):
        class LanguageView(SearchView):
            filter_backends = (LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request('/fr/search?q=article')
        assert 'fr' == request.LANGUAGE_CODE
        response = view(request)

        assert len(response.data['documents']) == response.data['count'] == 7
        assert 'fr' == response.data['documents'][0]['locale']

        request = self.get_request('/en-US/search?q=article')
        assert 'en-US' == request.LANGUAGE_CODE
        response = view(request)
        assert len(response.data['documents']) == response.data['count'] == 6
        assert 'en-US' == response.data['documents'][0]['locale']

    def test_language_filter_override(self):
        """Ensure locale override can find the only 'fr' document."""
        class LanguageView(SearchView):
            filter_backends = (SearchQueryBackend, LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request('/en-US/search?q=pipe&locale=*')
        assert 'en-US' == request.LANGUAGE_CODE
        response = view(request)

        assert len(response.data['documents']) == response.data['count'] == 1
        assert 'fr' == response.data['documents'][0]['locale']

        request = self.get_request('/en-US/search?q=pipe')
        assert 'en-US' == request.LANGUAGE_CODE
        response = view(request)
        assert len(response.data['documents']) == response.data['count'] == 0

    def test_database_filter(self):
        class DatabaseFilterView(SearchView):
            filter_backends = (DatabaseFilterBackend,)

        view = DatabaseFilterView.as_view()
        request = self.get_request('/en-US/search?group=tagged')
        response = view(request)
        assert len(response.data['documents']) == response.data['count'] == 2
        assert 'article-title' == response.data['documents'][0]['slug']
        assert [{
                'name': 'Group',
                'slug': 'group',
                'options': [{
                    'name': 'Tagged',
                    'slug': 'tagged',
                    'count': 2,
                    'active': True,
                    'urls': {
                        'active': '/en-US/search?group=tagged',
                        'inactive': '/en-US/search',
                    },
                }],
                },
                ] == response.data['filters']

        request = self.get_request('/fr/search?group=non-existent')
        response = view(request)
        assert len(response.data['documents']) == response.data['count'] == 7

    def test_get_filters(self):
        FilterGroup.objects.create(
            name='Topics',
            slug='topic',
            order=1)
        qd = QueryDict('q=test&topic=css,canvas,js')
        filters = get_filters(qd.getlist)
        assert [u'css,canvas,js'] == filters

        qd = QueryDict('q=test&topic=css,js&none=none')
        filters = get_filters(qd.getlist)
        assert [u'none'] == filters

        qd = QueryDict('q=test&none=none')
        filters = get_filters(qd.getlist)
        assert [u'none'] == filters
