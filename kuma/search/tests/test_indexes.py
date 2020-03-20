from django.conf import settings
from elasticsearch_dsl.connections import connections

from kuma.wiki.models import Document
from kuma.wiki.search import WikiDocumentType

from . import ElasticTestCase
from ..models import Index


class TestIndexes(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ["wiki/documents.json"]

    def tearDown(self):
        super(TestIndexes, self).tearDown()
        Index.objects.all().delete()

    def test_get_current(self):
        assert (
            "%s-main_index" % settings.ES_INDEX_PREFIX
            == Index.objects.get_current().prefixed_name
        )

    def _reload(self, index):
        return Index.objects.get(pk=index.pk)

    def test_add_newindex(self):
        index = Index.objects.create()
        assert not index.populated
        index.populate()
        index = self._reload(index)
        assert index.populated
        index.delete()

    def test_promote_index(self):
        index = Index.objects.create()
        index.populate()
        index = self._reload(index)
        assert index.populated
        index.promote()
        assert index.promoted

        assert index.prefixed_name == Index.objects.get_current().prefixed_name

        index.demote()
        assert not index.promoted

    def test_there_can_be_only_one(self):
        """Tests that when one index is promoted, all others are demoted."""
        index1 = Index.objects.get_current()
        assert index1.promoted

        index2 = Index.objects.create(name="second")
        index2.promote()
        index1 = self._reload(index1)
        assert index2.promoted
        assert not index1.promoted

    def test_outdated(self):
        # first create and populate an index
        main_index = Index.objects.create(name="first")
        main_index.populate()
        main_index = self._reload(main_index)
        assert main_index.populated
        main_index.promote()
        assert main_index.prefixed_name == Index.objects.get_current().prefixed_name

        # then create a successor and render a document against the old index
        successor_index = Index.objects.create(name="second")
        doc = Document.objects.get(pk=1)
        doc.title = "test outdated"
        doc.slug = "test-outdated"
        doc.save()
        doc.render()
        assert 1 == successor_index.outdated_objects.count()

        # .populate() creates the index and populates it.
        successor_index.populate()

        S = WikiDocumentType.search
        assert 7 == S(index=successor_index.prefixed_name).count()
        assert "lorem-ipsum" == S().query("match", title="lorem").execute()[0].slug

        # Promotion reindexes outdated documents. Test that our change is
        # reflected in the index.
        successor_index.promote()
        self.refresh(index=successor_index.prefixed_name)
        assert 0 == successor_index.outdated_objects.count()
        assert (
            "test-outdated"
            == S(index=successor_index.prefixed_name)
            .query("match", title="outdated")
            .execute()[0]
            .slug
        )

    def test_delete_index(self):
        # first create and populate the index
        index = Index.objects.create()
        index.populate()

        # then delete it and check if recreating works without blowing up
        index.delete()

        es = connections.get_connection()
        es.indices.create(index.prefixed_name)
        es.indices.delete(index.prefixed_name)
