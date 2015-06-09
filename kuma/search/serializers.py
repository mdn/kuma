import collections
from operator import attrgetter

from elasticsearch_dsl import document
from rest_framework import serializers, pagination
from tower import ugettext as _

from . import models
from .fields import LocaleField, SearchQueryField, SiteURLField
from .paginator import SearchPaginator
from .queries import Filter, FilterGroup
from .utils import QueryURLObject


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False)
    highlight = serializers.CharField(required=False)
    # Advanced search query paramenters.
    css_classnames = serializers.CharField(required=False)
    html_attributes = serializers.CharField(required=False)
    kumascript_macros = serializers.CharField(required=False)

    def validate_highlight(self, attrs, source):
        """
        The 'highlight' value should only be 'true' (default) or 'false'.
        """
        value = attrs.get(source)
        if value and value == 'false':
            value = False
        else:
            # If empty or any value other than 'false', we default to
            # highlighting enabled.
            value = True
        attrs[source] = value
        return attrs


class FilterURLSerializer(serializers.Serializer):
    active = serializers.CharField(read_only=True)
    inactive = serializers.CharField(read_only=True)


class FacetedFilterOptionsSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    active = serializers.BooleanField(read_only=True, default=False)
    urls = FilterURLSerializer(read_only=True)


class FacetedFilterSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    options = FacetedFilterOptionsSerializer(source='options', many=True)


class SearchSerializer(pagination.PaginationSerializer):
    results_field = 'documents'
    paginator_class = SearchPaginator

    query = SearchQueryField(source='*')
    page = serializers.Field(source='number')
    pages = serializers.Field(source='paginator.num_pages')
    start = serializers.Field(source='start_index')
    end = serializers.Field(source='end_index')
    locale = LocaleField(source='*')
    filters = serializers.SerializerMethodField('get_filters')

    def get_filters(self, obj):
        view = self.context['view']

        url = QueryURLObject(view.url)
        filter_mapping = collections.OrderedDict((filter_['slug'], filter_)
                                                 for filter_ in view.serialized_filters)

        filter_groups = collections.OrderedDict()

        try:
            facet_counts = [
                (k, getattr(obj, 'aggregations', {})[k]['doc_count'])
                for k in filter_mapping.keys()]
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
                filter_name = _(filter_['name'])
                group_name = _(filter_['group']['name'])
                group_slug = filter_['group']['slug']

            filter_groups.setdefault((
                group_name,
                group_slug,
                filter_['group']['order']
            ), []).append(
                Filter(url=url,
                       page=view.current_page,
                       name=filter_name,
                       slug=slug,
                       count=count,
                       active=slug in view.selected_filters,
                       group_name=group_name,
                       group_slug=group_slug)
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
        return FacetedFilterSerializer(
            sorted(grouped_filters, key=attrgetter('order'), reverse=True),
            many=True
        ).data


class BaseDocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, max_length=255)
    slug = serializers.CharField(read_only=True, max_length=255)
    locale = serializers.CharField(read_only=True, max_length=7)
    url = SiteURLField('wiki.document', args=['slug'])
    edit_url = SiteURLField('wiki.edit_document', args=['slug'])

    def field_to_native(self, obj, field_name):
        if field_name == 'parent' and not getattr(obj, 'parent', None):
            return {}
        # We have to convert the object to an actual dict here to make
        # sure the code in restframework works as it assumes a dict instance.
        if isinstance(obj, document.DocType):
            obj = obj.to_dict()
        return super(BaseDocumentSerializer,
                     self).field_to_native(obj, field_name)


class DocumentSerializer(BaseDocumentSerializer):
    excerpt = serializers.SerializerMethodField('get_excerpt')
    tags = serializers.ChoiceField(read_only=True, source='tags')
    score = serializers.FloatField(read_only=True, source='meta.score')
    explanation = serializers.SerializerMethodField('get_explanation')
    parent = BaseDocumentSerializer(read_only=True, source='parent')

    def get_excerpt(self, obj):
        return obj.get_excerpt()

    def get_explanation(self, obj):
        return getattr(obj.meta, 'explanation', None)


class FilterSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('get_localized_name')

    class Meta:
        model = models.Filter
        depth = 1
        fields = ('name', 'slug', 'shortcut')
        read_only_fields = ('slug', 'shortcut')

    def get_localized_name(self, obj):
        return _(obj.name)


class GroupWithFiltersSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('get_localized_name')
    slug = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)
    filters = FilterSerializer(source='filters.visible_only', read_only=True)

    class Meta:
        model = models.FilterGroup
        depth = 1
        fields = ('name', 'slug', 'order', 'filters')

    def get_localized_name(self, obj):
        return _(obj.name)


class GroupSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)


class FilterWithGroupSerializer(FilterSerializer):
    tags = serializers.SerializerMethodField('tag_names')
    group = GroupSerializer(source='group', read_only=True)

    def tag_names(self, obj):
        return [tag.name for tag in obj.tags.all()]

    class Meta(FilterSerializer.Meta):
        fields = FilterSerializer.Meta.fields + ('tags', 'operator', 'group')
