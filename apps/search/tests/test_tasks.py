# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from nose.tools import eq_

from search.tests import ElasticTestCase

from wiki.models import DocumentType
from wiki.tests import revision


class TestLiveIndexing(ElasticTestCase):

    fixtures = ['test_users.json',]

    def test_live_indexing_docs(self):
        S = DocumentType.search
        count_before = S().count()

        r = revision(save=True)
        self.refresh()
        eq_(count_before + 1, S().count())

        r.document.delete()
        self.refresh()
        eq_(count_before, S().count())
