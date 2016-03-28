import json
from collections import OrderedDict
from operator import attrgetter

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext
from django.views.decorators.cache import cache_page
from rest_framework.generics import ListAPIView
from rest_framework.renderers import JSONRenderer

from kuma.wiki.search import WikiDocumentType

from .filters import (AdvancedSearchQueryBackend, DatabaseFilterBackend,
                      HighlightFilterBackend, LanguageFilterBackend,
                      SearchQueryBackend, get_filters)
from .jobs import AvailableFiltersJob
from .pagination import SearchPagination
from .queries import Filter, FilterGroup
from .renderers import ExtendedTemplateHTMLRenderer
from .serializers import (DocumentSerializer, FacetedFilterSerializer,
                          FilterWithGroupSerializer, SearchQuerySerializer)
from .utils import QueryURLObject


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
    pagination_class = SearchPagination

    def initial(self, request, *args, **kwargs):
        super(SearchView, self).initial(request, *args, **kwargs)
        self.current_page = self.request.query_params.get(
            self.pagination_class.page_query_param,
            1,
        )
        self.available_filters = AvailableFiltersJob().get()
        self.serialized_filters = (
            FilterWithGroupSerializer(self.available_filters, many=True).data)
        self.selected_filters = get_filters(self.request.query_params.getlist)
        self.query_params = {}

    def get_queryset(self):
        return WikiDocumentType.search()

    def list(self, request, *args, **kwargs):
        """
        We override the `list` method here to store the URL.
        """
        # Stash some data here for the serializer.
        self.url = request.get_full_path()
        query_params = SearchQuerySerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        self.query_params = query_params.data
        return super(SearchView, self).list(request, *args, **kwargs)

    def get_filters(self, aggregations):
        url = QueryURLObject(self.url)
        filter_mapping = OrderedDict(
            (filter_['slug'], filter_)
            for filter_ in self.serialized_filters
        )
        filter_groups = OrderedDict()

        try:
            aggs = aggregations or {}
            facet_counts = [(slug, aggs[slug]['doc_count'])
                            for slug in filter_mapping.keys()]
        except KeyError:
            facet_counts = []

        for slug, count in facet_counts:

            filter_ = filter_mapping.get(slug, None)
            if filter_ is None:
                filter_name = slug
                group_name = None
                group_slug = None
            else:
                # Let's check if we can get the name from the gettext catalog
                filter_name = ugettext(filter_['name'])
                group_name = ugettext(filter_['group']['name'])
                group_slug = filter_['group']['slug']

            filter_groups.setdefault((
                group_name,
                group_slug,
                filter_['group']['order']
            ), []).append(
                Filter(
                    url=url,
                    page=self.current_page,
                    name=filter_name,
                    slug=slug,
                    count=count,
                    active=slug in self.selected_filters,
                    group_name=group_name,
                    group_slug=group_slug,
                )
            )

        # return a sorted list of filters here
        grouped_filters = []
        for group_options, filters in filter_groups.items():
            group_name, group_slug, group_order = group_options
            sorted_filters = sorted(filters, key=attrgetter('name'))
            grouped_filters.append(FilterGroup(name=group_name,
                                               slug=group_slug,
                                               order=group_order,
                                               options=sorted_filters))
        sorted_filters = sorted(grouped_filters,
                                key=attrgetter('order'),
                                reverse=True)
        return FacetedFilterSerializer(sorted_filters, many=True).data


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
        'locale': request.LANGUAGE_CODE
    }, content_type='application/opensearchdescription+xml')
