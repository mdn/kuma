from nose.tools import ok_, eq_

from kuma.wiki.search import WikiDocumentType

from . import ElasticTestCase
from ..fields import DocumentExcerptField, SearchQueryField, SiteURLField
from ..models import Filter, FilterGroup
from ..serializers import FilterWithGroupSerializer, DocumentSerializer


class SerializerTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ['wiki/documents.json',
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
            'group': {'name': 'Group', 'slug': 'group', 'order': 1},
            'shortcut': None})

    def test_document_serializer(self):
        search = WikiDocumentType.search()
        result = search.execute()
        doc_serializer = DocumentSerializer(result, many=True)
        list_data = doc_serializer.data
        eq_(len(list_data), 7)
        ok_(isinstance(list_data, list))
        ok_(1 in [data['id'] for data in list_data])

        doc_serializer = DocumentSerializer(result[0], many=False)
        dict_data = doc_serializer.data
        ok_(isinstance(dict_data, dict))
        eq_(dict_data['id'], result[0].id)


class FieldTests(ElasticTestCase):

    def test_DocumentExcerptField(self):

        class FakeValue(WikiDocumentType):
            summary = 'just a summary'
            highlight = {'content': ['this is <em>matching</em> text']}

        field = DocumentExcerptField()
        eq_(field.to_native(FakeValue()), 'this is <em>matching</em> text')

        class FakeValue(WikiDocumentType):
            summary = 'just a summary'
            highlight = {}

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

    def test_SiteURLField(self):
        class FakeValue(object):
            slug = 'Firefox'
            locale = 'de'

        field = SiteURLField('wiki.document', args=['slug'])
        value = field.to_native(FakeValue())
        ok_('/de/docs/Firefox' in value)
