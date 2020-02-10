from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .paginator import SearchPaginator


class SearchPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100
    page_size_query_param = "per_page"
    template = None
    django_paginator_class = SearchPaginator

    def paginate_queryset(self, queryset, request, view=None):
        """
        Stores the view to be able to call some methods of it
        in get_paginated_response. Does the default other than that.
        """
        self.view = view
        return super(SearchPagination, self).paginate_queryset(
            queryset, request, view=view
        )

    def get_paginated_response(self, data):
        return Response(
            {
                "query": self.request.query_params.get("q"),
                "locale": getattr(
                    self.request, "LANGUAGE_CODE", settings.WIKI_DEFAULT_LANGUAGE
                ),
                "page": self.page.number,
                "pages": self.page.paginator.num_pages,
                "start": self.page.start_index(),
                "end": self.page.end_index(),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "filters": self.view.get_filters(self.page.aggregations),
                "documents": data,
            }
        )
