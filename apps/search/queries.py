from collections import namedtuple
from operator import attrgetter
from django.utils.datastructures import SortedDict

from elasticutils.contrib.django import S
from tower import ugettext as _

from .utils import QueryURLObject


class Filter(namedtuple('Filter',
                        ['name', 'slug', 'count', 'url',
                         'page', 'active', 'group'])):
    __slots__ = ()

    def pop_page(self, url):
        return str(url.pop_query_param('page', str(self.page)))

    def urls(self):
        return {
            'active': self.pop_page(
                self.url.merge_query_param('topic', self.slug)),
            'inactive': self.pop_page(
                self.url.pop_query_param('topic', self.slug)),
        }


FilterGroup = namedtuple('FilterGroup', ['name', 'order', 'options'])


class DocumentS(S):
    """
    This S object acts more like Django's querysets to better match
    the behavior of restframework's serializers as well as adding a
    method to return our custom facets.
    """
    def __init__(self, *args, **kwargs):
        self.url = kwargs.pop('url', None)
        self.current_page = kwargs.pop('current_page', None)
        self.serialized_filters = kwargs.pop('serialized_filters', None)
        self.topics = kwargs.pop('topics', None)
        super(DocumentS, self).__init__(*args, **kwargs)

    def _clone(self, next_step=None):
        new = super(DocumentS, self)._clone(next_step)
        new.url = self.url
        new.current_page = self.current_page
        new.serialized_filters = self.serialized_filters
        new.topics = self.topics
        return new

    def all(self):
        """
        The serializer calls the ``all`` method for "all items" of the queryset,
        while elasticutils considers the method to return "all results" of the
        search, which ignores pagination etc.

        Iterating over self is the same as in Django's querysets' all method.
        """
        return self

    def faceted_filters(self):
        url = QueryURLObject(self.url)
        filter_mapping = SortedDict((filter_['slug'], filter_)
                                    for filter_ in self.serialized_filters)

        filter_groups = SortedDict()

        for slug, facet in self.facet_counts().items():
            if not isinstance(facet, dict):
                # let's just blankly ignore any non-filter or non-query filters
                continue

            filter_ = filter_mapping.get(slug, None)
            if filter_ is None:
                name = slug
                group = None
            else:
                # Let's check if we can get the name from the gettext catalog
                name = _(filter_['name'])
                group = _(filter_['group']['name'])

            f = Filter(url=url,
                       page=self.current_page,
                       name=name,
                       slug=slug,
                       count=facet.get('count', 0),
                       active=slug in self.topics,
                       group=group)

            filter_groups.setdefault((group, filter_['group']['order']), []).append(f)

        # return a sorted list of filters here
        grouped_filters = []
        for (group, order), filters in filter_groups.items():
            sorted_filters = sorted(filters, key=attrgetter('name'))
            grouped_filters.append(FilterGroup(group,
                                               order,
                                               sorted_filters))
        return sorted(grouped_filters, key=attrgetter('order'), reverse=True)
