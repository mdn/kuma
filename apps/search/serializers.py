from rest_framework import serializers, pagination

from .fields import (SearchQueryField, DocumentExcerptField,
                     TopicQueryField, LocaleField)
from .models import Filter


class FilterURLSerializer(serializers.Serializer):
    active = serializers.CharField(read_only=True)
    inactive = serializers.CharField(read_only=True)


class FacetedFilterSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    urls = FilterURLSerializer(read_only=True)


class FacetedFilterSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    options = FacetedFilterSerializer(source='options')


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


class DocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, max_length=255)
    slug = serializers.CharField(read_only=True, max_length=255)
    locale = serializers.CharField(read_only=True, max_length=7)
    excerpt = DocumentExcerptField(source='*')
    url = serializers.CharField(read_only=True, source='get_url')
    edit_url = serializers.CharField(read_only=True, source='get_edit_url')
    tags = serializers.ChoiceField(read_only=True, source='tags')
    score = serializers.FloatField(read_only=True, source='_score')
    explanation = serializers.CharField(read_only=True, source='_explanation')


class FilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Filter
        depth = 1
        fields = ('name', 'slug')
        read_only_fields = ('name', 'slug')


class GroupWithFiltersSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)
    filters = FilterSerializer(source='filters', read_only=True)

    class Meta:
        model = Filter
        depth = 1
        fields = ('name', 'order', 'filters')


class GroupSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)


class FilterWithGroupSerializer(FilterSerializer):
    tags = serializers.SerializerMethodField('tag_names')
    group = GroupSerializer(source='group', read_only=True)

    def tag_names(self, obj):
        return obj.tags.values_list('name', flat=True)

    class Meta(FilterSerializer.Meta):
        fields = FilterSerializer.Meta.fields + ('tags', 'operator', 'group')
