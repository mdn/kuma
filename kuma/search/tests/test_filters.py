from kuma.core.tests import eq_, ok_
from kuma.wiki.models import Document
from kuma.wiki.signals import render_done

from django.http import QueryDict

from . import ElasticTestCase
from ..filters import (AdvancedSearchQueryBackend, DatabaseFilterBackend,
                       HighlightFilterBackend, LanguageFilterBackend,
                       SearchQueryBackend, get_filters)
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
        eq_(response.data['count'], 4)
        eq_(len(response.data['documents']), 4)
        eq_(response.data['documents'][0]['slug'], 'CSS/article-title-3')
        eq_(response.data['documents'][0]['locale'], 'en-US')

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
        eq_(response.data['count'], 1)
        eq_(len(response.data['documents']), 1)
        eq_(response.data['documents'][0]['slug'], doc.slug)
        eq_(response.data['documents'][0]['locale'], doc.locale)

    def test_highlight_filter(self):
        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request('/en-US/search?q=article')
        response = view(request)
        ok_('<mark>article</mark>' in response.data['documents'][0]['excerpt'])

    def test_no_highlight_filter(self):
        class HighlightView(SearchView):
            filter_backends = (SearchQueryBackend, HighlightFilterBackend)

        view = HighlightView.as_view()
        request = self.get_request('/en-US/search?q=article&highlight=false')
        response = view(request)
        ok_('<mark>' not in response.data['documents'][0]['excerpt'])

    def test_language_filter(self):
        class LanguageView(SearchView):
            filter_backends = (LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request('/fr/search?q=article')
        eq_(request.LANGUAGE_CODE, 'fr')
        response = view(request)

        eq_(response.data['count'], 7)
        eq_(len(response.data['documents']), 7)
        eq_(response.data['documents'][0]['locale'], 'fr')

        request = self.get_request('/en-US/search?q=article')
        eq_(request.LANGUAGE_CODE, 'en-US')
        response = view(request)
        eq_(response.data['count'], 6)
        eq_(len(response.data['documents']), 6)
        eq_(response.data['documents'][0]['locale'], 'en-US')

    def test_language_filter_override(self):
        """Ensure locale override can find the only 'fr' document."""
        class LanguageView(SearchView):
            filter_backends = (SearchQueryBackend, LanguageFilterBackend,)

        view = LanguageView.as_view()
        request = self.get_request('/en-US/search?q=pipe&locale=*')
        eq_(request.LANGUAGE_CODE, 'en-US')
        response = view(request)

        eq_(response.data['count'], 1)
        eq_(len(response.data['documents']), 1)
        eq_(response.data['documents'][0]['locale'], 'fr')

        request = self.get_request('/en-US/search?q=pipe')
        eq_(request.LANGUAGE_CODE, 'en-US')
        response = view(request)
        eq_(response.data['count'], 0)
        eq_(len(response.data['documents']), 0)

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

    def test_get_filters(self):
        FilterGroup.objects.create(
            name='Topics',
            slug='topic',
            order=1)
        qd = QueryDict('q=test&topic=css,canvas,js')
        filters = get_filters(qd.getlist)
        eq_(filters, [u'css,canvas,js'])

        qd = QueryDict('q=test&topic=css,js&none=none')
        filters = get_filters(qd.getlist)
        eq_(filters, [u'none'])

        qd = QueryDict('q=test&none=none')
        filters = get_filters(qd.getlist)
        eq_(filters, [u'none'])
