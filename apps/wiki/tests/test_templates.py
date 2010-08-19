from nose.tools import eq_
from pyquery import PyQuery as pq

from wiki.models import Document
from wiki.tests import TestCaseBase, get


class DocumentTests(TestCaseBase):
    """Tests for the Document view/template"""

    def test_document_view(self):
        d = Document(title='Test Document', html='<div>Lorem Ipsum</div>',
                     category=1, locale='en-US')
        d.save()
        response = get(self.client, 'wiki.document', args=[d.id])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(d.title, doc('#main-content h1').text())
        eq_(pq(d.html)('div').text(), doc('#doc-content div').text())
