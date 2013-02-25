from nose.tools import eq_

from elasticutils.tests import ElasticTestCase

from wiki.models import DocumentType
from wiki.tests import document


class TestLiveIndexing(ElasticTestCase):

    def test_live_indexing_docs(self):
        S = DocumentType.search
        count_before = S().count()

        d = document(title='Testing live index', save=True)
        self.refresh()
        eq_(count_before + 1, S().count())

        d.delete()
        self.refresh()
        eq_(count_before, S().count())
