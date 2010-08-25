from django.contrib.auth.models import User

from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from wiki.models import Document, Revision, SIGNIFICANCES, CATEGORIES
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
        tags = ['tag1', 'tag2']
        data = self._new_document_data(tags)
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        d = Document.objects.get(title=data['title'])
        eq_([('http://testserver/en-US/kb/%s/history' % d.id, 302)],
            response.redirect_chain)
        eq_(data['category'], d.category)
        eq_(tags, list(d.tags.values_list('name', flat=True)))
        eq_(data['firefox_versions'],
            list(d.firefox_versions.values_list('item_id', flat=True)))
        eq_(data['operating_systems'],
            list(d.operating_systems.values_list('item_id', flat=True)))
        r = d.revisions.all()[0]
        eq_(data['keywords'], r.keywords)
        eq_(data['summary'], r.summary)
        eq_(data['content'], r.content)
        eq_(data['significance'], r.significance)

    def test_new_document_POST_empty_title(self):
        """Trigger required field validation for title."""
        self.client.login(username='admin', password='testpass')
        data = self._new_document_data(['tag1', 'tag2'])
        data['title'] = ''
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Please provide a title.', ul('li').text())

    def test_new_document_POST_empty_content(self):
        """Trigger required field validation for content."""
        self.client.login(username='admin', password='testpass')
        data = self._new_document_data(['tag1', 'tag2'])
        data['content'] = ''
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Please provide content.', ul('li').text())

    def test_new_document_POST_invalid_category(self):
        """Try to create a new document with an invalid category value."""
        self.client.login(username='admin', password='testpass')
        data = self._new_document_data(['tag1', 'tag2'])
        data['category'] = 963
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Select a valid choice. 963 is not one of the available choices.',
            ul('li').text())

    def test_new_document_POST_invalid_ff_version(self):
        """Try to create a new document with an invalid firefox version."""
        self.client.login(username='admin', password='testpass')
        data = self._new_document_data(['tag1', 'tag2'])
        data['firefox_versions'] = [1337]
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Select a valid choice. 1337 is not one of the available choices.',
            ul('li').text())

    def _new_document_data(self, tags):
        return {
            'title': 'A Test Article',
            'tags': ','.join(tags),
            'firefox_versions': [1, 2],
            'operating_systems': [1, 3],
            'category': CATEGORIES[0][0],
            'keywords': 'key1, key2',
            'summary': 'lipsum',
            'content': 'lorem ipsum dolor sit amet',
            'significance': SIGNIFICANCES[0][0],
        }


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
        eq_(1, d.revisions.count())


class DocumentListTests(TestCaseBase):
    """Tests for the All and Category template"""

    def test_category_list(self):
        """Verify the category documents list view."""
        d = _create_document()
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
