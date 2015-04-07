import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer

from kuma.wiki.search import WikiDocumentType

from .exceptions import ValidationError
from .filters import (AdvancedSearchQueryBackend, DatabaseFilterBackend,
                      get_filters, HighlightFilterBackend,
                      LanguageFilterBackend, SearchQueryBackend)
from .jobs import AvailableFiltersJob
from .paginator import SearchPaginator
from .renderers import ExtendedTemplateHTMLRenderer
from .serializers import (DocumentSerializer, FilterWithGroupSerializer,
                          SearchQuerySerializer, SearchSerializer)


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
        SearchQueryBackend,
        AdvancedSearchQueryBackend,
        DatabaseFilterBackend,
        LanguageFilterBackend,
        HighlightFilterBackend,
    )
    paginator_class = SearchPaginator
    paginate_by = 10
    max_paginate_by = 100
    paginate_by_param = 'per_page'
    pagination_serializer_class = SearchSerializer

    def initial(self, request, *args, **kwargs):
        super(SearchView, self).initial(request, *args, **kwargs)
        self.current_page = self.request.QUERY_PARAMS.get(self.page_kwarg, 1)
        self.available_filters = AvailableFiltersJob().get()
        self.serialized_filters = (
            FilterWithGroupSerializer(self.available_filters, many=True).data)
        self.selected_filters = get_filters(self.request.QUERY_PARAMS.getlist)
        self.query_params = {}

    def get_queryset(self):
        return WikiDocumentType.search()

    def list(self, request, *args, **kwargs):
        """
        We override the `list` method here to store the URL.
        """
        # Stash some data here for the serializer.
        self.url = request.get_full_path()
        query_params = SearchQuerySerializer(data=request.QUERY_PARAMS)
        if not query_params.is_valid():
            raise ValidationError(query_params.errors)
        self.query_params = query_params.data

        return super(SearchView, self).list(request, *args, **kwargs)


search = SearchView.as_view()


@cache_page(60 * 15)  # 15 minutes.
def suggestions(request):
    """Return empty array until we restore internal search system."""

    content_type = 'application/x-suggestions+json'

    term = request.GET.get('q')
    if not term:
        return HttpResponseBadRequest(content_type=content_type)

    results = []
    return HttpResponse(json.dumps(results), content_type=content_type)


@cache_page(60 * 60 * 168)  # 1 week.
def plugin(request):
    """Render an OpenSearch Plugin."""
    return render(request, 'search/plugin.html', {
        'locale': request.locale
    }, content_type='application/opensearchdescription+xml')
