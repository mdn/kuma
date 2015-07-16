# -*- coding: utf-8 -*-
import elasticsearch
from nose.tools import eq_
from . import ElasticTestCase
from ..models import Index, Filter, FilterGroup
from ..views import SearchView


class ViewTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ['wiki/documents.json',
                                           'search/filters.json']

    def test_search_rendering(self):
        """The search view """
        # self.refresh()
        response = self.client.get('/en-US/search?q=test')
        eq_(response.status_code, 200)
        self.assertContains(response, 'Results for')

        response = self.client.get('/en-US/search?q=article')
        eq_(response.status_code, 200)
        self.assertContains(response, 'an article title')

    def test_search_filters(self):
        response = self.client.get('/en-US/search?q=article')
        eq_(response.status_code, 200)
        self.assertContains(response,
                            '4 documents found for "article" in English')

    def test_serialized_filters(self):

        class Test1SearchView(SearchView):
            filter_backends = ()

            def dispatch(self, *args, **kwargs):
                super(Test1SearchView, self).dispatch(*args, **kwargs)
                eq_(self.serialized_filters,
                    [{'name': 'Tagged',
                      'slug': 'tagged',
                      'tags': ['tagged'],
                      'operator': 'OR',
                      'group': {'name': 'Group', 'slug': 'group', 'order': 1},
                      'shortcut': None
                      }])

        test_view1 = Test1SearchView.as_view()
        test_view1(self.get_request('/en-US/'))

        group = FilterGroup.objects.get(name='Group')
        Filter.objects.create(name='Serializer', slug='serializer',
                              group=group)

        class Test2SearchView(SearchView):
            filter_backends = ()

            def dispatch(self, *args, **kwargs):
                super(Test2SearchView, self).dispatch(*args, **kwargs)
                eq_(self.serialized_filters,
                    [{'name': 'Tagged',
                      'slug': 'tagged',
                      'tags': ['tagged'],
                      'operator': 'OR',
                      'group': {'name': 'Group', 'slug': 'group', 'order': 1},
                      'shortcut': None},
                     {'name': 'Serializer',
                      'slug': 'serializer',
                      'tags': [],
                      'operator': 'OR',
                      'group': {'name': 'Group', 'slug': 'group', 'order': 1},
                      'shortcut': None
                      }])

        test_view2 = Test2SearchView.as_view()
        test_view2(self.get_request('/en-US/'))

    def test_filters(self):

        class FilterSearchView(SearchView):
            expected = None
            filter_backends = ()

            def dispatch(self, *args, **kwargs):
                super(FilterSearchView, self).dispatch(*args, **kwargs)
                eq_(self.selected_filters, self.expected)

        view = FilterSearchView.as_view(expected=['spam'])
        view(self.get_request('/en-US/?group=spam'))

        # the filters are deduplicated
        view = FilterSearchView.as_view(expected=['spam', 'eggs'])
        view(self.get_request('/en-US/?group=spam&group=eggs'))
        view(self.get_request('/en-US/?group=spam&group=eggs&group=spam'))

    def test_queryset(self):

        class QuerysetSearchView(SearchView):
            def list(self, *args, **kwargs):
                response = super(QuerysetSearchView, self).list(*args,
                                                                **kwargs)
                data = response.data

                # queryset content
                docs = data['documents']
                eq_(docs[0]['title'], 'an article title')
                eq_(docs[0]['locale'], 'en-US')

                # metadata
                eq_(self.current_page, 1)
                eq_(len(self.serialized_filters), 1)
                eq_(self.selected_filters, ['tagged'])
                eq_(self.url, self.request.get_full_path())

                # aggregations
                filters = data['filters']
                eq_(len(filters), 1)
                eq_(filters[0]['name'], 'Group')
                eq_(filters[0]['options'][0]['name'], 'Tagged')
                eq_(filters[0]['options'][0]['count'], 2)
                eq_(filters[0]['options'][0]['active'], True)
                return response

        view = QuerysetSearchView.as_view()
        request = self.get_request('/en-US/search?q=article&group=tagged')
        view(request)

    def test_allowed_methods(self):
        response = self.client.get('/en-US/search?q=test')
        eq_(response.status_code, 200)

        response = self.client.head('/en-US/search?q=test')
        eq_(response.status_code, 405)

        response = self.client.post('/en-US/search?q=test')
        eq_(response.status_code, 405)

    def test_handled_exceptions(self):

        # These are instantiated with an error string.
        for exc in [elasticsearch.ElasticsearchException,
                    elasticsearch.SerializationError,
                    elasticsearch.TransportError,
                    elasticsearch.NotFoundError,
                    elasticsearch.RequestError]:

            class ExceptionSearchView(SearchView):
                filter_backends = ()

                def list(self, *args, **kwargs):
                    raise exc(503, 'ERROR!!')

            view = ExceptionSearchView.as_view()
            request = self.get_request('/en-US/search')
            response = view(request)
            self.assertContains(response,
                                'Search is temporarily unavailable',
                                status_code=200)

    def test_unicode_exception(self):
        class UnicodeDecodeErrorSearchView(SearchView):
            filter_backends = ()

            def list(self, *args, **kwargs):
                # willfully causing a UnicodeDecodeError
                return 'coöperative'.encode('ascii')

        view = UnicodeDecodeErrorSearchView.as_view()
        request = self.get_request('/en-US/search')
        response = view(request)
        self.assertContains(response,
                            'Something went wrong with the search query',
                            status_code=404)

    def test_unhandled_exceptions(self):
        class RealExceptionSearchView(SearchView):
            filter_backends = ()

            def list(self, *args, **kwargs):
                raise ValueError

        view = RealExceptionSearchView.as_view()
        request = self.get_request('/en-US/search')
        self.assertRaises(ValueError, view, request)

    def test_paginate_by_param(self):
        request = self.get_request('/en-US/search')
        view = SearchView.as_view(paginate_by=1)
        response = view(request)
        eq_(response.data['pages'], 6)

        request = self.get_request('/en-US/search?per_page=4')
        response = view(request)
        eq_(response.data['pages'], 2)

    def test_tokenize_camelcase_titles(self):
        for q in ('get', 'element', 'by', 'id'):
            response = self.client.get('/en-US/search?q=' + q)
            eq_(response.status_code, 200)
            self.assertContains(response, 'camel-case-test')

    def test_index(self):
        self.client.login(username='admin', password='testpass')
        response = self.client.get('/en-US/search')
        eq_(response.status_code, 200)
        self.assertContains(response,
                            ('Search index: %s' %
                             Index.objects.get_current().name))
