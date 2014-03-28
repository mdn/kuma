import operator
from django.conf import settings
from django.utils.datastructures import SortedDict

from elasticutils import Q
from elasticutils.contrib.django import F
from rest_framework.filters import BaseFilterBackend
from waffle import flag_is_active

from search.models import DocumentType, Filter, FilterGroup


def get_filters(getter_func):
    filters = SortedDict()
    for slug in FilterGroup.objects.values_list('slug', flat=True):
        for filters_slug in getter_func(slug, []):
            filters[filters_slug] = None
    return filters.keys()


class LanguageFilterBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given queryset
    based on the current request's locale, or a different locale (or none at
    all) specified by query parameter
    """
    def filter_queryset(self, request, queryset, view):
        locale = request.GET.get('locale', None)
        if '*' == locale:
            return queryset
        if not locale or locale not in settings.MDN_LANGUAGES:
            locale = request.locale
        return queryset.filter(locale=locale)


class SearchQueryBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given
    queryset based on the search query found in the current request's
    query parameters.
    """
    search_param = 'q'
    search_operations = [
        ('title__match', 6.0),
        ('summary__match', 2.0),
        ('content__match', 1.0),
        ('title__match_phrase', 10.0),
        ('content__match_phrase', 8.0),
    ]

    def filter_queryset(self, request, queryset, view):
        search_param = request.QUERY_PARAMS.get(self.search_param, None)

        if search_param:
            queries = {}
            boosts = {}
            for operation, boost in self.search_operations:
                queries[operation] = search_param
                boosts[operation] = boost
            queryset = (queryset.query(Q(should=True, **queries))
                                .boost(**boosts))
        if flag_is_active(request, 'search_explanation'):
            queryset = queryset.explain()  # adds scoring explaination
        return queryset


class AdvancedSearchQueryBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given queryset
    based on additional query parameters that correspond to advanced search
    indexes.
    """
    search_params = (
        'kumascript_macros',
        'css_classnames',
        'html_attributes',
    )
    search_operations = [
        ('%s__match', 10.0),
        ('%s__prefix', 5.0),
    ]

    def filter_queryset(self, request, queryset, view):
        queries = {}
        boosts = {}

        for name in self.search_params:

            search_param = request.QUERY_PARAMS.get(name, None)
            if not search_param:
                continue

            for operation_tmpl, boost in self.search_operations:
                operation = operation_tmpl % name
                queries[operation] = search_param.lower()
                boosts[operation] = boost

        queryset = (queryset.query(Q(should=True, **queries))
                            .boost(**boosts))

        return queryset


class HighlightFilterBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that applies highlighting
    based on the excerpt fields of the Document search index.
    """
    highlight_fields = DocumentType.excerpt_fields

    def filter_queryset(self, request, queryset, view):
        return queryset.highlight(*self.highlight_fields)


class DatabaseFilterBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given
    queryset based on the filters stored in the database.

    If there are more than one tag attached to the filter it will
    use the filter's operator to determine which logical operation to
    use with those tags. The default is OR.

    It then applies custom facets based on those database filters
    but will ignore non-raw facets.
    """
    def filter_queryset(self, request, queryset, view):
        active_filters = []
        active_facets = []

        for serialized_filter in view.serialized_filters:
            filter_tags = serialized_filter['tags']
            filter_operator = Filter.OPERATORS[serialized_filter['operator']]
            if serialized_filter['slug'] in view.selected_filters:

                if len(filter_tags) > 1:
                    tag_filters = []
                    for filter_tag in filter_tags:
                        tag_filters.append(F(tags=filter_tag))
                    active_filters.append(reduce(filter_operator, tag_filters))
                else:
                    active_filters.append(F(tags=filter_tags[0]))

            if len(filter_tags) > 1:
                facet_params = {
                    'or': {
                        'filters': [
                            {'term': {'tags': tag}}
                            for tag in filter_tags
                        ],
                        '_cache': True,
                    },
                }
            else:
                facet_params = {
                    'term': {'tags': filter_tags[0]}
                }
            active_facets.append((serialized_filter['slug'], facet_params))

        if view.drilldown_faceting:
            filter_operator = operator.and_
        else:
            filter_operator = operator.or_

        unfiltered_queryset = queryset
        if active_filters:
            queryset = queryset.filter(reduce(filter_operator, active_filters))

        # only way to get to the currently applied filters
        # to use it to limit the facets filters below
        if view.drilldown_faceting:
            facet_filter = queryset._build_query().get('filter', [])
        else:
            facet_filter = unfiltered_queryset._build_query().get('filter', [])

        for facet_slug, facet_params in active_facets:
            facet_query = {
                facet_slug: {
                    'filter': facet_params,
                    'facet_filter': facet_filter,
                }
            }
            queryset = queryset.facet_raw(**facet_query)

        return queryset
