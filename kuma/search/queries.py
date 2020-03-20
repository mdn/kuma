from collections import namedtuple


class Filter(
    namedtuple(
        "Filter",
        ["name", "slug", "count", "url", "page", "active", "group_name", "group_slug"],
    )
):
    __slots__ = ()

    def pop_page(self, url):
        return str(url.pop_query_param("page", str(self.page)))

    def urls(self):
        return {
            "active": self.pop_page(
                self.url.merge_query_param(self.group_slug, self.slug)
            ),
            "inactive": self.pop_page(
                self.url.pop_query_param(self.group_slug, self.slug)
            ),
        }


FilterGroup = namedtuple("FilterGroup", ["name", "slug", "order", "options"])
