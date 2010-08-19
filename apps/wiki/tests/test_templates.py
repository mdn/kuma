from nose.tools import eq_

from wiki.tests import TestCaseBase, get


class DocumentTests(TestCaseBase):
    """Tests for the Document view/template"""

    def test_document_view(self):
        response = get(self.client, 'wiki.document', args=[1])
        eq_(200, response.status_code)
