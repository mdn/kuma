from nose.tools import ok_

from sumo.middleware import LocaleURLMiddleware
from waffle.models import Flag

from search.tests import ElasticTestCase, factory
from search.views import SearchView

from search.filters import (SearchQueryBackend, HighlightFilterBackend,
                            LanguageFilterBackend, DatabaseFilterBackend)


class FilterTests(ElasticTestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def setUp(self):
        super(FilterTests, self).setUp()
        Flag.objects.create(name='elasticsearch', everyone=True)

    def test_search_query(self):
        class SearchQueryView(SearchView):
            filter_backends = (SearchQueryBackend,)

        view = SearchQueryView.as_view()
        request = factory.get('/en-US/search?q=article')
        response = view(request)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(len(response.data['documents']), 4)
        self.assertEqual(response.data['documents'][0]['slug'], 'article-title')
        self.assertEqual(response.data['documents'][0]['locale'], 'en-US')

    def test_highlight_filter(self):

        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = factory.get('/en-US/search?q=article')
        response = view(request)
        ok_('<em>article</em>' in response.data['documents'][0]['excerpt'])

    def test_language_filter(self):
        class LanguageView(SearchView):
            filter_backends = (LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = factory.get('/fr/search?q=article')
        # setting request.locale correctly
        LocaleURLMiddleware().process_request(request)
        response = view(request)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['documents']), 1)
        self.assertEqual(response.data['documents'][0]['locale'], 'fr')

        request = factory.get('/en-US/search?q=article')
        # setting request.locale correctly
        LocaleURLMiddleware().process_request(request)
        response = view(request)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(len(response.data['documents']), 5)
        self.assertEqual(response.data['documents'][0]['locale'], 'en-US')

    def test_database_filter(self):
        class DatabaseFilterView(SearchView):
            filter_backends = (DatabaseFilterBackend,)

        view = DatabaseFilterView.as_view()
        request = factory.get('/en-US/search?topic=tagged')
        response = view(request)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['documents']), 2)
        self.assertEqual(response.data['documents'][0]['slug'], 'article-title')
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

        request = factory.get('/fr/search?topic=non-existent')
        response = view(request)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['documents']), 6)
        self.assertEqual(response.data['documents'][0]['slug'], 'le-title')
