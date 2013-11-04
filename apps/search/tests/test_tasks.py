from nose.tools import eq_

from search.tests import ElasticTestCase

from wiki.tests import revision

from search.models import DocumentType


class TestLiveIndexing(ElasticTestCase):
    fixtures = ['test_users.json']

    def test_live_indexing_docs(self):
        S = DocumentType.search
        count_before = S().count()

        r = revision(save=True)
        r.document.render()

        self.refresh()
        eq_(count_before + 1, S().count())

        r.document.delete()
        self.refresh()
        eq_(count_before, S().count())
