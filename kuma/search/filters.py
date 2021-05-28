from django.conf import settings
from elasticsearch_dsl import Q, query
from rest_framework.filters import BaseFilterBackend

from .models import Filter, FilterGroup


def get_filters(getter_func):
    """
    Returns the values of all filter groups, intended to pull key/value pairs
    from requests.

    E.g. if 'topic' is a `FilterGroup` slug and given the URL::

        ?q=test&topic=css&topic=html

    this will return `['css', 'html']`.

    If the given URL contains 'none', then no filters should be applied.

    """
    if getter_func("none"):
        return ["none"]
    filters = {}
    for slug in FilterGroup.objects.values_list("slug", flat=True):
        for filters_slug in getter_func(slug, []):
            filters[filters_slug] = None
    if filters:
        return filters.keys()
    else:
        # Given a list of [<group_slug>, <tag_slug>, <shortcut>] we only want
        # the tags.
        return [x[1] for x in Filter.objects.default_filters()]


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
        locale = request.GET.get("locale", None)
        if "*" == locale:
            return queryset

        sq = queryset.to_dict().pop("query", query.MatchAll().to_dict())

        if request.LANGUAGE_CODE == settings.LANGUAGE_CODE:
            locales = [request.LANGUAGE_CODE]
        else:
            locales = [request.LANGUAGE_CODE, settings.LANGUAGE_CODE]

        positive_sq = {"bool": {"must": sq, "filter": {"terms": {"locale": locales}}}}
        negative_sq = {
            "bool": {"must_not": [{"term": {"locale": request.LANGUAGE_CODE}}]}
        }
        # Note: Here we are replacing the query rather than calling
        # `queryset.query` which would result in a boolean must query.
        queryset.query = query.Boosting(
            positive=positive_sq, negative=negative_sq, negative_boost=0.5
        )
        return queryset


class SearchQueryBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given
    queryset based on the search query found in the current request's
    query parameters.
    """

    search_operations = [
        # (<query type>, <field>, <boost factor>)
        ("match", "title", 7.2),
        ("match", "summary", 2.0),
        ("match", "content", 1.0),
        ("match_phrase", "title", 12.0),
        ("match_phrase", "content", 8.0),
    ]

    def filter_queryset(self, request, queryset, view):
        search_term = view.query_params.get("q")

        if search_term:
            queries = []
            for query_type, field, boost in self.search_operations:
                queries.append(
                    Q(query_type, **{field: {"query": search_term, "boost": boost}})
                )
            queryset = queryset.query(
                "function_score",
                query=query.Bool(should=queries),
                functions=[query.SF("field_value_factor", field="boost")],
            )

        if request.user.is_superuser:
            queryset = queryset.extra(explain=True)

        return queryset


class KeywordQueryBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given queryset
    based on additional query parameters that correspond to case-insensitive
    keywords.
    """

    fields = (
        "css_classnames",
        "html_attributes",
    )

    def filter_queryset(self, request, queryset, view):
        queries = []

        for field in self.fields:
            raw_search_param = view.query_params.get(field, "").lower()
            wildcard = "*" in raw_search_param or "?" in raw_search_param
            search_param = raw_search_param.replace("*", "").replace("?", "")
            if not search_param:
                # Skip if not given, or just wildcard
                continue

            # Exact match of sanitized value
            queries.append(Q("term", **{field: {"value": search_param, "boost": 10.0}}))
            if wildcard:
                # Wildcard search of value as passed
                queries.append(
                    Q("wildcard", **{field: {"value": raw_search_param, "boost": 5.0}})
                )
        if queries:
            queryset = queryset.query(query.Bool(should=queries))

        return queryset


class TagGroupFilterBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that filters the given
    queryset based on named tag groups.

    If there are more than one tag attached to the filter it will
    use the filter's operator to determine which logical operation to
    use with those tags. The default is OR.

    It then applies custom aggregations based on those database filters
    but will ignore non-raw aggregations.
    """

    def filter_queryset(self, request, queryset, view):
        active_filters = []
        active_facets = []

        for serialized_filter in view.serialized_filters:
            filter_tags = serialized_filter["tags"]
            if not filter_tags:
                # Incomplete filter has no tags, skip it
                continue

            if serialized_filter["slug"] in view.selected_filters:
                # User selected this filter - filter on the associated tags
                tag_filters = []
                for filter_tag in filter_tags:
                    tag_filters.append(Q("term", tags=filter_tag))

                filter_operator = Filter.OPERATORS[serialized_filter["operator"]]
                if len(tag_filters) > 1 and filter_operator == "and":
                    # Add an AND filter as a subclause
                    active_filters.append(Q("bool", must=tag_filters))
                else:
                    # Extend list of tags for the OR clause
                    active_filters.extend(tag_filters)

            # Aggregate counts for active filters for sidebar
            if len(filter_tags) > 1:
                facet_params = Q("terms", tags=list(filter_tags))
            else:
                facet_params = Q("term", tags=filter_tags[0])
            active_facets.append((serialized_filter["slug"], facet_params))

        # Count documents across all tags
        for facet_slug, facet_params in active_facets:
            queryset.aggs.bucket(facet_slug, "filter", **facet_params.to_dict())

        # Filter by tag only after counting documents across all tags
        if active_filters:
            if len(active_filters) == 1:
                queryset = queryset.post_filter(active_filters[0])
            else:
                queryset = queryset.post_filter(Q("bool", should=active_filters))

        return queryset


class HighlightFilterBackend(BaseFilterBackend):
    """
    A django-rest-framework filter backend that adds search term highlighting.
    """

    def filter_queryset(self, request, queryset, view):
        raise NotImplementedError
