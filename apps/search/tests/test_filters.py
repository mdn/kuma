from nose.tools import ok_

from waffle.models import Flag

from search.filters import (SearchQueryBackend, HighlightFilterBackend,
                            LanguageFilterBackend, DatabaseFilterBackend)
from search.tests import ElasticTestCase
from search.views import SearchView


class FilterTests(ElasticTestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def setUp(self):
        super(FilterTests, self).setUp()
        Flag.objects.create(name='elasticsearch', everyone=True)

    def test_search_query(self):
        class SearchQueryView(SearchView):
            filter_backends = (SearchQueryBackend,)

        view = SearchQueryView.as_view()
        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(len(response.data['documents']), 4)
        self.assertEqual(response.data['documents'][1]['slug'],
                         'article-title')
        self.assertEqual(response.data['documents'][1]['locale'], 'en-US')

    def test_highlight_filter(self):

        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        ok_('<em>article</em>' in response.data['documents'][1]['excerpt'])

    def test_language_filter(self):
        class LanguageView(SearchView):
            filter_backends = (LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request('/fr/search?q=article')
        response = view(request)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['documents']), 1)
        self.assertEqual(response.data['documents'][0]['locale'], 'fr')

        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['documents']), 6)
        self.assertEqual(response.data['documents'][0]['locale'], 'en-US')

    def test_database_filter(self):
        class DatabaseFilterView(SearchView):
            filter_backends = (DatabaseFilterBackend,)

        view = DatabaseFilterView.as_view()
        request = self.get_request('/en-US/search?topic=tagged')
        response = view(request)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['documents']), 2)
        self.assertEqual(response.data['documents'][0]['slug'],
                         'article-title')
        self.assertEqual(response.data['filters'], [
            {
                'name': 'Group',
                'options': [{
                    'name': 'Tagged',
                    'slug': 'tagged',
                    'count': 2,
                    'active': True,
                    'urls': {
                        'active': '/en-US/search?topic=tagged',
                        'inactive': '/en-US/search',
                    },
                }],
            },
        ])

        request = self.get_request('/fr/search?topic=non-existent')
        response = view(request)
        self.assertEqual(response.data['count'], 7)
        self.assertEqual(len(response.data['documents']), 7)
        self.assertEqual(response.data['documents'][0]['slug'], 'le-title')
