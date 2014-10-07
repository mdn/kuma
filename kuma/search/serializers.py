from rest_framework import serializers, pagination

from .fields import (SearchQueryField, DocumentExcerptField,
                     LocaleField, SiteURLField)
from .models import Filter, FilterGroup


class FilterURLSerializer(serializers.Serializer):
    active = serializers.CharField(read_only=True)
    inactive = serializers.CharField(read_only=True)


class FacetedFilterOptionsSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    urls = FilterURLSerializer(read_only=True)


class FacetedFilterSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    options = FacetedFilterOptionsSerializer(source='options')


class SearchSerializer(pagination.PaginationSerializer):
    results_field = 'documents'

    query = SearchQueryField(source='*')
    page = serializers.Field(source='number')
    pages = serializers.Field(source='paginator.num_pages')
    start = serializers.Field(source='start_index')
    end = serializers.Field(source='end_index')
    locale = LocaleField(source='*')
    filters = FacetedFilterSerializer(source='paginator.object_list.'
                                             'faceted_filters',
                                      many=True)


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
        return super(BaseDocumentSerializer, self).field_to_native(obj, field_name)


class DocumentSerializer(BaseDocumentSerializer):
    excerpt = DocumentExcerptField(source='*')
    tags = serializers.ChoiceField(read_only=True, source='tags')
    score = serializers.FloatField(read_only=True, source='es_meta.score')
    explanation = serializers.CharField(read_only=True,
                                        source='es_meta.explanation')
    parent = BaseDocumentSerializer(read_only=True,
                                    source='parent')


class FilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Filter
        depth = 1
        fields = ('name', 'slug', 'shortcut')
        read_only_fields = ('name', 'slug', 'shortcut')


class GroupWithFiltersSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)
    filters = FilterSerializer(source='filters.visible_only', read_only=True)

    class Meta:
        model = FilterGroup
        depth = 1
        fields = ('name', 'slug', 'order', 'filters')


class GroupSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)


class FilterWithGroupSerializer(FilterSerializer):
    tags = serializers.SerializerMethodField('tag_names')
    group = GroupSerializer(source='group', read_only=True)

    def tag_names(self, obj):
        return obj.tags.values_list('name', flat=True)

    class Meta(FilterSerializer.Meta):
        fields = FilterSerializer.Meta.fields + ('tags', 'operator', 'group')
