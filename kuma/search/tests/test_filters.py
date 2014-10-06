from nose.tools import ok_, eq_

from . import ElasticTestCase
from ..filters import (SearchQueryBackend, HighlightFilterBackend,
                       LanguageFilterBackend, DatabaseFilterBackend)
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
        eq_(response.data['count'], 4)
        eq_(len(response.data['documents']), 4)
        eq_(response.data['documents'][0]['slug'], 'article-title')
        eq_(response.data['documents'][0]['locale'], 'en-US')

    def test_highlight_filter(self):

        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        ok_('<em>article</em>' in response.data['documents'][0]['excerpt'])

    def test_language_filter(self):
        class LanguageView(SearchView):
            filter_backends = (LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request('/fr/search?q=article')
        eq_(request.locale, 'fr')
        response = view(request)

        eq_(response.data['count'], 7)
        eq_(len(response.data['documents']), 7)
        eq_(response.data['documents'][0]['locale'], 'fr')

        request = self.get_request('/en-US/search?q=article')
        eq_(request.locale, 'en-US')
        response = view(request)
        eq_(response.data['count'], 6)
        eq_(len(response.data['documents']), 6)
        eq_(response.data['documents'][0]['locale'], 'en-US')

    def test_database_filter(self):
        class DatabaseFilterView(SearchView):
            filter_backends = (DatabaseFilterBackend,)

        view = DatabaseFilterView.as_view()
        request = self.get_request('/en-US/search?group=tagged')
        response = view(request)
        eq_(response.data['count'], 2)
        eq_(len(response.data['documents']), 2)
        eq_(response.data['documents'][0]['slug'], 'article-title')
        eq_(response.data['filters'], [
            {
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
        ])

        request = self.get_request('/fr/search?group=non-existent')
        response = view(request)
        eq_(response.data['count'], 7)
        eq_(len(response.data['documents']), 7)
