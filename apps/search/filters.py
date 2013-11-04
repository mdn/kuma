import operator
from elasticutils import Q
from elasticutils.contrib.django import F

from rest_framework.filters import BaseFilterBackend

from search.models import DocumentType, Filter


class LanguageFilterBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given
    queryset based on the current request's locale
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(locale=request.locale)


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
        if request.user.is_superuser:
            queryset = queryset.explain()  # adds scoring explaination
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
            if serialized_filter['slug'] in view.current_topics:

                if len(filter_tags) > 1:
                    tag_filters = []
                    for filter_tag in filter_tags:
                        tag_filters.append(F(tags=filter_tag.lower()))
                    active_filters.append(reduce(filter_operator, tag_filters))
                else:
                    active_filters.append(F(tags=filter_tags[0].lower()))

            if len(filter_tags) > 1:
                facet_params = {
                    'or': {
                        'filters': [
                            {'term': {'tags': tag.lower()}}
                            for tag in filter_tags
                        ],
                        '_cache': True,
                    },
                }
            else:
                facet_params = {
                    'term': {'tags': filter_tags[0].lower()}
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
