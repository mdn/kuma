import json

from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from rest_framework.generics import ListAPIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from waffle import flag_is_active

from .filters import (LanguageFilterBackend, SearchFilterBackend,
                      SearchQueryBackend, HighlightFilterBackend)
from .models import Filter, DocumentType
from .serializers import SearchSerializer, DocumentSerializer, FilterSerializer
from .queries import DocumentS


class SearchView(ListAPIView):
    http_method_names = ['get']
    serializer_class = DocumentSerializer
    renderer_classes = (
        TemplateHTMLRenderer,
        JSONRenderer,
    )
    #: list of filters to applies in order of listing, each implementing
    #: the specific search feature
    filter_backends = (
        LanguageFilterBackend,
        SearchQueryBackend,
        HighlightFilterBackend,
        SearchFilterBackend,
    )
    paginate_by = 10
    max_paginate_by = 100
    paginate_by_param = 'per_page'
    pagination_serializer_class = SearchSerializer
    topic_param = 'topic'
    result_page = 'search/results.html'
    search_param = 'q'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Google Custom Search results page
        if not flag_is_active(request, 'elasticsearch'):
            query = request.GET.get('q', '')
            return render(request, 'landing/searchresults.html',
                          {'query': query})
        return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_parse_query(self):
        query = self.request.QUERY_PARAMS.get(self.search_param, None)
        allowed_slugs = map(lambda slug: slug.lower(),
                            self.available_filters.values_list('slug',
                                                               flat=True))
        token_filters = []
        token_query = []
        if query:
            for token in query.split(' '):
                if token.startswith('#') and token[1:] in allowed_slugs:
                    token_filters.append(token[1:])
                else:
                    token_query.append(token)
        return 'u '.join(token_query), token_filters

    def initial(self, request, *args, **kwargs):
        super(SearchView, self).initial(request, *args, **kwargs)
        self.drilldown_faceting = flag_is_active(request,
                                                 'search_drilldown_faceting')
        self.available_filters = (Filter.objects.prefetch_related('tags',
                                                                  'group')
                                                .filter(enabled=True))
        self.serialized_filters = FilterSerializer(self.available_filters,
                                                   many=True).data
        self.current_page = self.request.QUERY_PARAMS.get(self.page_kwarg, 1)
        self.search_query, self.token_filters = self.get_parse_query()
        topics = self.request.QUERY_PARAMS.getlist(self.topic_param, [])
        seen_topics = set()
        self.current_topics = [topic for topic in topics + self.token_filters
                               if (topic not in seen_topics and
                                   not seen_topics.add(topic))]
        if flag_is_active(request, 'redesign'):
            self.result_page = 'search/results-redesign.html'

    def get_template_names(self):
        return [self.result_page]

    def get_queryset(self):
        return DocumentS(DocumentType,
                         url=self.request.get_full_path(),
                         current_page=self.current_page,
                         serialized_filters=self.serialized_filters,
                         topics=self.current_topics)

search = SearchView.as_view()


@cache_page(60 * 15)  # 15 minutes.
def suggestions(request):
    """Return empty array until we restore internal search system."""

    mimetype = 'application/x-suggestions+json'

    term = request.GET.get('q')
    if not term:
        return HttpResponseBadRequest(mimetype=mimetype)

    results = []
    return HttpResponse(json.dumps(results), mimetype=mimetype)


@cache_page(60 * 60 * 168)  # 1 week.
def plugin(request):
    """Render an OpenSearch Plugin."""
    site = Site.objects.get_current()
    return render(request, 'search/plugin.html', {
        'site': site,
        'locale': request.locale
    }, content_type='application/opensearchdescription+xml')
