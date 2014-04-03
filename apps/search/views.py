import json

from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer
from waffle import flag_is_active

from .filters import (LanguageFilterBackend, DatabaseFilterBackend,
                      SearchQueryBackend, HighlightFilterBackend,
                      AdvancedSearchQueryBackend, get_filters)
from .models import Filter, DocumentType
from .renderers import ExtendedTemplateHTMLRenderer
from .serializers import SearchSerializer, DocumentSerializer, FilterSerializer
from .queries import DocumentS


class SearchView(ListAPIView):
    http_method_names = ['get']
    serializer_class = DocumentSerializer
    renderer_classes = (
        ExtendedTemplateHTMLRenderer,
        JSONRenderer,
    )
    #: list of filters to applies in order of listing, each implementing
    #: the specific search feature
    filter_backends = (
        LanguageFilterBackend,
        SearchQueryBackend,
        AdvancedSearchQueryBackend,
        HighlightFilterBackend,
        DatabaseFilterBackend,
    )
    paginate_by = 10
    max_paginate_by = 100
    paginate_by_param = 'per_page'
    pagination_serializer_class = SearchSerializer

    def initial(self, request, *args, **kwargs):
        super(SearchView, self).initial(request, *args, **kwargs)
        self.current_page = self.request.QUERY_PARAMS.get(self.page_kwarg, 1)
        self.drilldown_faceting = flag_is_active(request,
                                                 'search_drilldown_faceting')
        self.available_filters = (Filter.objects.prefetch_related('tags',
                                                                  'group')
                                                .filter(enabled=True))
        self.serialized_filters = FilterSerializer(self.available_filters,
                                                   many=True).data
        self.selected_filters = get_filters(self.request.QUERY_PARAMS.getlist)

    def get_queryset(self):
        return DocumentS(DocumentType,
                         url=self.request.get_full_path(),
                         current_page=self.current_page,
                         serialized_filters=self.serialized_filters,
                         selected_filters=self.selected_filters)

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
