from unittest import mock

from django.conf import settings
from django.utils import translation
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from kuma.wiki.search import WikiDocumentType

from . import ElasticTestCase
from ..fields import SearchQueryField, SiteURLField
from ..models import Filter, FilterGroup
from ..serializers import (DocumentSerializer, FilterSerializer,
                           FilterWithGroupSerializer, SearchQuerySerializer)


class SerializerTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ['wiki/documents.json',
                                           'search/filters.json']

    def test_filter_serializer(self):
        group = FilterGroup.objects.get(name='Group')
        filter_ = Filter.objects.create(name='Serializer', slug='serializer',
                                        group=group)
        filter_.tags.add('tag')
        filter_serializer = FilterWithGroupSerializer(filter_)
        data = filter_serializer.data
        assert ({'order': 1, 'name': 'Group', 'slug': 'group'} ==
                data['group'])
        assert 'Serializer' == data['name']
        assert 'OR' == data['operator']
        assert data['shortcut'] is None
        assert 'serializer' == data['slug']
        assert 1 == len(data['tags'])
        assert 'tag' == data['tags'][0]

    @mock.patch('kuma.search.serializers.ugettext')
    def test_filter_serializer_with_translations(self, _mock):
        _mock.return_value = 'Juegos'
        translation.activate('es')
        filter_ = Filter(name='Games', slug='games')
        serializer = FilterSerializer(filter_)
        assert {
            'name': 'Juegos',
            'slug': 'games',
            'shortcut': None
        } == serializer.data

    def test_document_serializer(self):
        search = WikiDocumentType.search()
        result = search.execute()
        doc_serializer = DocumentSerializer(result, many=True)
        list_data = doc_serializer.data
        assert 7 == len(list_data)
        assert isinstance(list_data, list)
        assert 1 in [data['id'] for data in list_data]

        doc_serializer = DocumentSerializer(result[0], many=False)
        dict_data = doc_serializer.data
        assert isinstance(dict_data, dict)
        assert dict_data['id'] == result[0].id

    def test_search_query_serializer(self):
        search_serializer = SearchQuerySerializer(
            data={'q': 'test'}
        )
        assert search_serializer.is_valid()
        assert search_serializer.errors == {}

        search_serializer = SearchQuerySerializer(
            data={'q': r'test\nsomething'}
        )
        assert not search_serializer.is_valid()
        assert list(search_serializer.errors.keys()) == ['q']

        search_serializer = SearchQuerySerializer(
            data={'q': 't' * (settings.ES_Q_MAXLENGTH + 1)}
        )
        assert not search_serializer.is_valid()
        assert list(search_serializer.errors.keys()) == ['q']

    def test_excerpt(self):
        search = WikiDocumentType.search()
        search = search.query('match', summary='CSS')
        search = search.highlight(*WikiDocumentType.excerpt_fields)
        result = search.execute()
        serializer = DocumentSerializer(result, many=True)
        assert 'A <em>CSS</em> article' == serializer.data[0]['excerpt']


class SearchQueryFieldSerializer(serializers.Serializer):
    q = SearchQueryField()


class FieldTests(ElasticTestCase):

    def test_SearchQueryField(self):
        request = APIRequestFactory().get('/?q=test')
        # APIRequestFactory doesn't actually return APIRequest objects
        # but standard HttpRequest objects due to the way it initializes
        # the request when APIViews are called
        request.query_params = request.GET
        serializer = SearchQueryFieldSerializer(
            data={},
            context={'request': request},
        )
        serializer.is_valid()
        assert {'q': 'test'} == serializer.data

    def test_SiteURLField(self):
        class FakeValue(object):
            slug = 'Firefox'
            locale = 'de'

        field = SiteURLField('wiki.document', args=['slug'])
        value = field.to_representation(FakeValue())
        assert '/de/docs/Firefox' in value
