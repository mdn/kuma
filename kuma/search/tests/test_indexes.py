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

    def _reload(self, index):
        return Index.objects.get(pk=index.pk)

    def test_add_newindex(self):
        index = Index.objects.create()
        ok_(not index.populated)
        index.populate()
        index = self._reload(index)
        ok_(index.populated)
        index.delete()

    def test_promote_index(self):
        index = Index.objects.create()
        index.populate()
        index = self._reload(index)
        ok_(index.populated)
        index.promote()
        ok_(index.promoted)

        eq_(Index.objects.get_current().prefixed_name, index.prefixed_name)

        index.demote()
        ok_(not index.promoted)

    def test_there_can_be_only_one(self):
        """Tests that when one index is promoted, all others are demoted."""
        index1 = Index.objects.get_current()
        ok_(index1.promoted)

        index2 = Index.objects.create(name='second')
        index2.promote()
        index1 = self._reload(index1)
        ok_(index2.promoted)
        ok_(not index1.promoted)

    def test_outdated(self):
        # first create and populate an index
        main_index = Index.objects.create(name='first')
        main_index.populate()
        main_index = self._reload(main_index)
        ok_(main_index.populated)
        main_index.promote()
        eq_(Index.objects.get_current().prefixed_name,
            main_index.prefixed_name)

        # then create a successor and render a document against the old index
        successor_index = Index.objects.create(name='second')
        doc = Document.objects.get(pk=1)
        doc.title = 'test outdated'
        doc.slug = 'test-outdated'
        doc.save()
        doc.render()
        eq_(successor_index.outdated_objects.count(), 1)

        # .populate() creates the index and populates it.
        successor_index.populate()

        S = WikiDocumentType.search
        eq_(S(index=successor_index.prefixed_name).count(), 7)
        eq_(S().query('match', title='lorem').execute()[0].slug, 'lorem-ipsum')

        # Promotion reindexes outdated documents. Test that our change is
        # reflected in the index.
        successor_index.promote()
        self.refresh(index=successor_index.prefixed_name)
        eq_(successor_index.outdated_objects.count(), 0)
        eq_(S(index=successor_index.prefixed_name)
            .query('match', title='outdated').execute()[0].slug,
            'test-outdated')

    def test_delete_index(self):
        # first create and populate the index
        index = Index.objects.create()
        index.populate()

        # then delete it and check if recreating works without blowing up
        index.delete()

        es = connections.get_connection()
        try:
            es.indices.create(index.prefixed_name)
        except RequestError:
            assert False
        es.indices.delete(index.prefixed_name)
