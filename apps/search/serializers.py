from rest_framework import serializers, pagination

from .fields import SearchQueryField, TopicQueryField, DocumentExcerptField
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
    topics = TopicQueryField(source='*')
    page = serializers.Field(source='number')
    pages = serializers.Field(source='paginator.num_pages')
    start = serializers.Field(source='start_index')
    end = serializers.Field(source='end_index')
    filters = FacetedFilterSerializer(source='paginator.object_list.'
                                             'faceted_filters',
                                      many=True)


class DocumentSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True, max_length=255)
    slug = serializers.CharField(read_only=True, max_length=255)
    locale = serializers.CharField(read_only=True, max_length=7)
    excerpt = DocumentExcerptField(source='*')
    url = serializers.CharField(read_only=True, source='get_url')
    tags = serializers.ChoiceField(read_only=True, source='tags')
    score = serializers.FloatField(read_only=True, source='_score')
    explanation = serializers.CharField(read_only=True, source='_explanation')


class FilterGroupSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    order = serializers.CharField(read_only=True)


class FilterSerializer(serializers.ModelSerializer):
    tags = serializers.ChoiceField(source='tags.all', read_only=True)
    group = FilterGroupSerializer(source='group', read_only=True)

    class Meta:
        model = Filter
        depth = 1
        fields = ('name', 'slug', 'tags', 'operator', 'group')
        read_only_fields = ('name', 'slug', 'operator')
