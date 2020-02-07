from django.core.paginator import (
    EmptyPage,
    InvalidPage,
    Page,
    PageNotAnInteger,
    Paginator,
)
from django.utils.functional import cached_property


class SearchPaginator(Paginator):
    """
    A better paginator for search results

    The normal Paginator does a .count() query and then a slice. Since ES
    results contain the total number of results, we can take an optimistic
    slice and then adjust the count.
    """

    def __init__(self, *args, **kwargs):
        super(SearchPaginator, self).__init__(*args, **kwargs)
        self._result_total = None

    def validate_number(self, number):
        """
        Validates the given 1-based page number.

        We also check that the number isn't too large.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger("That page number is not an integer")
        if number < 1:
            raise EmptyPage("That page number is less than 1")

        if number >= 1000:
            # Anything >=1,000 will result in a hard error in
            # Elasticsearch which would happen before we even get a chance
            # to validate that the range is too big. The error you would
            # get from Elasticsearch 6.x is something like this:
            #
            #     Result window is too large, from + size must be less
            #     than or equal to: [10000] but was [11000].
            #
            # See https://github.com/mdn/kuma/issues/6092
            raise InvalidPage("Page number too large")

        return number

    def page(self, number):
        """
        Returns a page object.

        This class overrides the default behavior and ignores "orphans" and
        assigns the count from the ES result to the Paginator.
        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page

        # Force the search to evaluate and then attach the count. We want to
        # avoid an extra useless query even if there are no results, so we
        # directly fetch the count from hits.
        result = self.object_list[bottom:top].execute()
        page = Page(result.hits, number, self)
        # Set the count to the results after post_filter
        self._result_total = result.hits.total
        # Also store the aggregations, if any.
        page.aggregations = getattr(result, "aggregations", None)

        # Now that we have the count validate that the page number isn't higher
        # than the possible number of pages and adjust accordingly.
        if number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage("That page contains no results")
        return page

    @cached_property
    def count(self):
        """
        Returns the total number of results.

        Paginator's count property will call .count() on the search object,
        which returns results before the pre_filter. This will result in a
        count that is too high. Instead, use 'total' from the results,
        executing if needed.
        """
        if self._result_total is not None:
            return self._result_total
        return self.object_list.execute().hits.total
