from nose.tools import eq_, ok_

from django.conf import settings

from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import RequestError

from kuma.wiki.models import Document
from kuma.wiki.search import WikiDocumentType

from . import ElasticTestCase
from ..models import Index


class TestIndexes(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ['wiki/documents.json']

    def tearDown(self):
        super(TestIndexes, self).tearDown()
        Index.objects.all().delete()

    def test_get_current(self):
        eq_(Index.objects.get_current().prefixed_name,
            '%s-main_index' % settings.ES_INDEX_PREFIX)

    def test_add_newindex(self):
        index = Index.objects.create()
        ok_(not index.populated)
        index.populate()
        index = Index.objects.get(pk=index.pk)  # reload the index again
        ok_(index.populated)
        index.delete()

    def test_promote_index(self):
        index = Index.objects.create()
        index.populate()
        index = Index.objects.get(pk=index.pk)  # reload the index again
        ok_(index.populated)
        index.promote()
        ok_(index.promoted)

        eq_(Index.objects.get_current().prefixed_name, index.prefixed_name)

        index.demote()
        ok_(not index.promoted)
        main_name = '%s-main_index' % settings.ES_INDEX_PREFIX
        eq_(Index.objects.get_current().prefixed_name, main_name)
        index.delete()

    def test_outdated(self):
        # first create and populate an index
        main_index = Index.objects.create()
        main_index.populate()
        main_index = Index.objects.get(pk=main_index.pk)
        ok_(main_index.populated)
        main_index.promote()
        eq_(Index.objects.get_current().prefixed_name,
            main_index.prefixed_name)

        # then create a successor and render a document against the old index
        successor_index = Index.objects.create()
        doc = Document.objects.get(pk=1)
        doc.render()
        eq_(successor_index.outdated_objects.count(), 1)

        # then populate the successor and see if we still have outdated objects
        successor_index.populate()
        successor_index = Index.objects.get(pk=successor_index.pk)

        S = WikiDocumentType.search

        # check if the newly created index is empty
        eq_(S(index=successor_index.prefixed_name).count(), 0)

        successor_index.promote()
        eq_(successor_index.outdated_objects.count(), 0)

        self.refresh()  # refresh to make sure the index has the results ready
        eq_(S().count(), 7)
        eq_(S().query('match', title='lorem ipsum').execute()[0].slug,
            'lorem-ipsum')

    def test_delete_index(self):
        # first create and populate the index
        index = Index.objects.create()
        index.populate()

        # then create it again and see if it blows up
        es = connections.get_connection()

        # then delete it and check if recreating works without blowing up
        index.delete()
        try:
            es.indices.create(index.prefixed_name)
        except RequestError:
            assert False
        es.indices.delete(index.prefixed_name)
