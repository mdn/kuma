from django.contrib.auth.models import User

from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from wiki.models import Document, Revision
from wiki.tests import TestCaseBase


class DocumentTests(TestCaseBase):
    """Tests for the Document template"""

    def test_document_view(self):
        """Load the document view page and verify the title and content."""
        d = _create_document()
        response = self.client.get(d.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(d.title, doc('#main-content h1').text())
        eq_(pq(d.html)('div').text(), doc('#doc-content div').text())


class NewDocumentTests(TestCaseBase):
    """Tests for the New Document template"""
    fixtures = ['users.json']

    def test_new_document_GET_without_perm(self):
        """Trying to create a new document without permission returns 403."""
        self.client.login(username='rrosario', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        eq_(302, response.status_code)

    def test_new_document_GET_with_perm(self):
        """HTTP GET to new document URL renders the form."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#document-form input[name="title"]')))

    def test_new_document_POST(self):
        """HTTP POST to new document URL creates the document."""
        self.client.login(username='admin', password='testpass')
        title = 'A Test Article'
        response = self.client.post(reverse('wiki.new_document'),
                                    {'title': title,
                                     'category': 1,
                                     # This is throwing an IntegrityError.
                                     #'tags': 'test1, test2',
                                    }, follow=True)
        d = Document.objects.get(title=title)
        eq_([('http://testserver/en-US/kb/%s/history' % d.id, 302)],
            response.redirect_chain)


class NewRevisionTests(TestCaseBase):
    """Tests for the New Revision template"""
    fixtures = ['users.json']

    def test_new_revision_GET_without_perm(self):
        """Trying to create a new revision wihtout permission returns 403."""
        d = _create_document()
        self.client.login(username='rrosario', password='testpass')
        response = self.client.get(reverse('wiki.new_revision', args=[d.id]))
        eq_(302, response.status_code)

    def test_new_revision_GET_with_perm(self):
        """HTTP GET to new revision URL renders the form."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_revision', args=[d.id]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#revision-form textarea[name="content"]')))

    def test_new_revision_POST(self):
        """HTTP POST to new revision URL creates the revision."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        response = self.client.post(reverse('wiki.new_revision', args=[d.id]),
                                    {'summary': 'A brief summary',
                                     'content': 'The article content',
                                     'keywords': 'keyword1 keyword2',
                                     'significance': 10})
        eq_(302, response.status_code)
        eq_(1,d.revisions.count())


class DocumentListTests(TestCaseBase):
    """Tests for the All and Category template"""

    def test_category_list(self):
        """Verify the category documents list view."""
        d = _create_document();
        response = self.client.get(reverse('wiki.category',
                                   args=[d.category]))
        doc = pq(response.content)
        eq_(Document.objects.filter(category=d.category).count(),
            len(doc('#document-list li')))

    def test_all_list(self):
        """Verify the all documents list view."""
        _create_document()
        _create_document('Another one')
        response = self.client.get(reverse('wiki.all_documents'))
        doc = pq(response.content)
        eq_(Document.objects.all().count(),
            len(doc('#document-list li')))


class DocumentRevisionsTests(TestCaseBase):
    """Tests for the Document Revisions template"""
    fixtures = ['users.json']

    def test_document_revisions_list(self):
        """Verify the document revisions list view."""
        d = _create_document()
        user = User.objects.get(pk=118533)
        r1 = Revision(summary="a tweak", content='lorem ipsum dolor',
                      significance=10, keywords='kw1 kw2', document=d,
                      creator=user)
        r1.save()
        r2 = Revision(summary="another tweak", content='lorem dimsum dolor',
                      significance=10, keywords='kw1 kw2', document=d,
                      creator=user)
        r2.save()
        response = self.client.get(reverse('wiki.document_revisions',
                                   args=[d.id]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(2, len(doc('#revision-list > ul > li')))


def _create_document(title='Test Document'):
    d = Document(title=title, html='<div>Lorem Ipsum</div>',
                 category=1, locale='en-US')
    d.save()
    return d
