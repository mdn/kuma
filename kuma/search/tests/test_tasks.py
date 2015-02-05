from nose.tools import eq_

from kuma.wiki.search import WikiDocumentType
from kuma.wiki.tests import revision

from . import ElasticTestCase
from ..models import Index


class TestLiveIndexing(ElasticTestCase):

    def test_live_indexing_docs(self):
        # Live indexing uses tasks which pass the index by pk, so we need to
        # create and save one to the database here.
        index = Index.objects.create(promoted=True, populated=True)
        index.populate()

        S = WikiDocumentType.search
        count_before = S().count()

        r = revision(save=True)
        r.document.render()

        self.refresh()
        eq_(count_before + 1, S().count())

        r.document.delete()
        self.refresh()
        # TODO: Investigate this test failure. The ES debug output appears to
        # be doing the correct thing but the ES delete call is returning a 404.
        eq_(count_before, S().count())
