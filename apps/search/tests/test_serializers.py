from nose.tools import ok_, eq_

from search.models import Filter, FilterGroup
from search.tests import ElasticTestCase

from search.fields import DocumentExcerptField, SearchQueryField
from search.models import DocumentType
from search.serializers import FilterWithGroupSerializer, DocumentSerializer
from search.queries import DocumentS


class SerializerTests(ElasticTestCase):
    fixtures = ['test_users.json', 'wiki/documents.json',
                'search/filters.json']

    def test_filter_serializer(self):
        group = FilterGroup.objects.get(name='Group')
        filter_ = Filter.objects.create(name='Serializer', slug='serializer',
                                        group=group)
        filter_.tags.add('tag')
        filter_serializer = FilterWithGroupSerializer(filter_)
        eq_(filter_serializer.data, {
            'name': 'Serializer',
            'slug': 'serializer',
            'tags': ['tag'],
            'operator': 'OR',
            'group': {'name': 'Group', 'slug': 'group', 'order': 1}})

    def test_document_serializer(self):
        doc = DocumentS(DocumentType)
        doc_serializer = DocumentSerializer(doc, many=True)
        list_data = doc_serializer.data
        eq_(len(list_data), 7)
        ok_(isinstance(list_data, list))
        eq_(list_data[0]['title'], 'le title')

        doc_serializer = DocumentSerializer(doc[0], many=False)
        dict_data = doc_serializer.data
        ok_(isinstance(dict_data, dict))
        eq_(dict_data['title'], 'le title')


class FieldTests(ElasticTestCase):

    def test_DocumentExcerptField(self):

        class Meta(object):
            def __init__(self, highlight):
                self.highlight = highlight

        class FakeValue(DocumentType):
            summary = 'just a summary'
            es_meta = Meta({'content': ['this is <em>matching</em> text']})

        field = DocumentExcerptField()
        eq_(field.to_native(FakeValue()), 'this is <em>matching</em> text')

        class FakeValue(DocumentType):
            summary = 'just a summary'
            es_meta = Meta({})

        eq_(field.to_native(FakeValue()), FakeValue.summary)

    def test_SearchQueryField(self):
        request = self.get_request('/?q=test')
        # APIRequestFactory doesn't actually return APIRequest objects
        # but standard HttpRequest objects due to the way it initializes
        # the request when APIViews are called
        request.QUERY_PARAMS = request.GET

        field = SearchQueryField()
        field.context = {'request': request}
        eq_(field.to_native(None), 'test')
