from django.conf import settings
from django.utils.datastructures import SortedDict

from elasticsearch_dsl import F, Q, query
from rest_framework.filters import BaseFilterBackend
from waffle import flag_is_active

from .models import Filter, FilterGroup


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

    First, we bail if the locale query parameter is set to *. It's a short cut
    for the macros search.

    Then, if the current language is the standard language (English) we only
    show those documents.

    But if the current language is any non-standard language (non-English)
    we're limiting the documents to either English or the requested
    language, effectively filtering out all other languages. We also boost
    the non-English documents to show up before the English ones.

    """
    def filter_queryset(self, request, queryset, view):
        locale = request.GET.get('locale', None)
        if '*' == locale:
            return queryset

        sq = queryset.to_dict().pop('query', query.MatchAll().to_dict())

        if request.locale == settings.LANGUAGE_CODE:
            locales = [request.locale]
        else:
            locales = [request.locale, settings.LANGUAGE_CODE]

        positive_sq = {
            'filtered': {
                'query': sq,
                'filter': {'terms': {'locale': locales}}
            }
        }
        negative_sq = {
            'bool': {
                'must_not': [
                    {'term': {'locale': request.locale}}
                ]
            }
        }
        # Note: Here we are replacing the query rather than calling
        # `queryset.query` which would result in a boolean must query.
        queryset.query = query.Boosting(positive=positive_sq,
                                        negative=negative_sq,
                                        negative_boost=0.5)
        return queryset


class SearchQueryBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given
    queryset based on the search query found in the current request's
    query parameters.
    """
    search_param = 'q'
    search_operations = [
        # (<query type>, <field>, <boost factor>)
        ('match', 'title', 6.0),
        ('match', 'summary', 2.0),
        ('match', 'content', 1.0),
        ('match_phrase', 'title', 10.0),
        ('match_phrase', 'content', 8.0),
    ]

    def filter_queryset(self, request, queryset, view):
        search_param = request.QUERY_PARAMS.get(self.search_param, None)

        if search_param:
            queries = []
            for query_type, field, boost in self.search_operations:
                queries.append(
                    Q(query_type, **{field: {'query': search_param,
                                             'boost': boost}}))
            queryset = queryset.query(
                'function_score',
                query=query.Bool(should=queries),
                functions=[query.SF('field_value_factor', field='boost')],
            )

        if flag_is_active(request, 'search_explanation'):
            queryset = queryset.extra(explain=True)

        return queryset


class AdvancedSearchQueryBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given queryset
    based on additional query parameters that correspond to advanced search
    indexes.
    """
    fields = (
        'kumascript_macros',
        'css_classnames',
        'html_attributes',
    )
    search_operations = [
        # (<query_type>, <boost>)
        ('match', 10.0),
        ('prefix', 5.0),
    ]

    def filter_queryset(self, request, queryset, view):
        queries = []
        for field in self.fields:

            search_param = request.QUERY_PARAMS.get(field, None)
            if not search_param:
                continue
            search_param = search_param.lower()

            for query_type, boost in self.search_operations:
                queries.append(
                    Q(query_type, **{field: {'query': search_param,
                                             'boost': boost}}))

        if queries:
            queryset = queryset.query(query.Bool(should=queries))

        return queryset


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
                        tag_filters.append(F('term', tags=filter_tag))
                    active_filters.append(F(filter_operator, tag_filters))
                else:
                    active_filters.append(F('term', tags=filter_tags[0]))

            if len(filter_tags) > 1:
                facet_params = F('terms', tags=filter_tags)
            else:
                facet_params = F('term', tags=filter_tags[0])
            active_facets.append((serialized_filter['slug'], facet_params))

        unfiltered_queryset = queryset
        if active_filters:
            if len(active_filters) == 1:
                queryset = queryset.post_filter(active_filters[0])
            else:
                queryset = queryset.post_filter(F('or', active_filters))

        # only way to get to the currently applied filters
        # to use it to limit the facets filters below
        facet_filter = unfiltered_queryset.to_dict().get('filter', [])

        # TODO: Convert to use aggregations.
        facets = {}
        for facet_slug, facet_params in active_facets:
            facets[facet_slug] = {
                'filter': facet_params.to_dict(),
                'facet_filter': facet_filter,
            }
        queryset = queryset.extra(facets=facets)

        return queryset
