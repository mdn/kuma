from django.contrib.auth.models import User
from django.conf import settings

from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.tests import post, get
from wiki.models import Document, Revision, SIGNIFICANCES, CATEGORIES
from wiki.tests import TestCaseBase, document, revision
from wiki.forms import DocumentForm, RevisionForm
from wiki.views import _process_doc_and_rev_form


class DocumentTests(TestCaseBase):
    """Tests for the Document template"""
    fixtures = ['users.json']

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
        data = _new_document_data(tags)
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        d = Document.objects.get(title=data['title'])
        eq_([('http://testserver/en-US/kb/%s/history' % d.slug, 302)],
            response.redirect_chain)
        eq_(settings.WIKI_DEFAULT_LANGUAGE, d.locale)
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

    def test_new_document_other_locale(self):
        """Make sure we can create a document in a non-default locale."""
        self.client.login(username='admin', password='testpass')
        data = _new_document_data(['tag1', 'tag2'])
        locale = 'es'
        response = self.client.post(reverse('wiki.new_document', 
                                            locale=locale),
                                    data, follow=True)
        d = Document.objects.get(title=data['title'])
        eq_(locale, d.locale)

    def test_new_document_POST_empty_title(self):
        """Trigger required field validation for title."""
        self.client.login(username='admin', password='testpass')
        data = _new_document_data(['tag1', 'tag2'])
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
        data = _new_document_data(['tag1', 'tag2'])
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
        data = _new_document_data(['tag1', 'tag2'])
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
        data = _new_document_data(['tag1', 'tag2'])
        data['firefox_versions'] = [1337]
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('#document-form > form > ul.errorlist')
        eq_(1, len(ul))
        eq_('Select a valid choice. 1337 is not one of the available choices.',
            ul('li').text())

    def test_doc_and_rev_form_processing(self):
        """Test the helper function that persists the forms."""
        user = User.objects.get(pk=118533)

        # First we test the helper with a document in the default language.
        # This should create the document and revision.
        locale = settings.WIKI_DEFAULT_LANGUAGE
        tags = ['t1', 't2']
        data = _new_document_data(tags)
        doc_form = DocumentForm(data)
        rev_form = RevisionForm(data)
        assert doc_form.is_valid() and rev_form.is_valid()
        _process_doc_and_rev_form(doc_form, rev_form, locale, user,
                                  None, None)
        doc = Document.objects.get(slug=data['slug'], locale=locale)
        rev = doc.revisions.all()[0]
        _verify_doc_and_rev_data(data, doc, rev)
        eq_(tags, list(doc.tags.values_list('name', flat=True)))
        eq_(user, rev.creator)

        # Now we test the helper translating a document to Spanish. This
        # should create a new document with parent set to the document
        # created above and a revision based_on the revision created above.
        locale = 'es'
        data.update({'title': 'nuevo titulo', 'slug': 'nuevo-titulo',
                     'content': 'la traduccion del contenido',
                     'summary': 'el resumen'})
        doc_form = DocumentForm(data)
        rev_form = RevisionForm(data)
        assert doc_form.is_valid() and rev_form.is_valid()
        _process_doc_and_rev_form(doc_form, rev_form, locale, user,
                                  doc, rev)
        doc_es = Document.objects.get(slug=data['slug'], locale=locale)
        rev_es = doc_es.revisions.all()[0]
        _verify_doc_and_rev_data(data, doc_es, rev_es)
        eq_(doc, doc_es.parent)
        eq_(rev, rev_es.based_on)


class NewRevisionTests(TestCaseBase):
    """Tests for the New Revision template"""
    fixtures = ['users.json']

    def setUp(self):
        super(NewRevisionTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def test_new_revision_GET_without_perm(self):
        """Try to create a new revision without permission."""
        self.client.login(username='rrosario', password='testpass')
        response = self.client.get(reverse('wiki.new_revision',
                                           args=[self.d.slug]))
        eq_(302, response.status_code)

    def test_new_revision_GET_with_perm(self):
        """HTTP GET to new revision URL renders the form."""
        response = self.client.get(reverse('wiki.new_revision',
                                           args=[self.d.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#document-form textarea[name="content"]')))

    def test_new_revision_GET_based_on(self):
        """HTTP GET to new revision URL based on another revision.

        This case should render the form with the fields pre-populated
        with the based-on revision info.

        """
        r = Revision(document=self.d, keywords='ky1, kw2',
                     summary='the summary', significance=SIGNIFICANCES[0][0],
                     content='<div>The content here</div>', creator_id=118577)
        r.save()
        response = self.client.get(reverse('wiki.new_revision_based_on',
                                           args=[self.d.slug, r.id]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(doc('#id_keywords')[0].value, r.keywords)
        eq_(doc('#id_summary')[0].value, r.summary)
        eq_(doc('#id_content')[0].value, r.content)

    def test_new_revision_POST_document_with_current(self):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case already has a current_revision, therefore
        the document document fields are not editable.

        """
        response = self.client.post(
            reverse('wiki.new_revision', args=[self.d.slug]),
            {'summary': 'A brief summary', 'content': 'The article content',
             'keywords': 'keyword1 keyword2',
             'significance': SIGNIFICANCES[0][0]})
        eq_(302, response.status_code)
        eq_(2, self.d.revisions.count())

        new_rev = self.d.revisions.order_by('-id')[0]
        eq_(self.d.current_revision, new_rev.based_on)

    def test_new_revision_POST_document_without_current(self):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case doesn't have a current_revision, therefore
        the document fields are open for editing.

        """
        rev = self.d.current_revision
        self.d.current_revision = None
        self.d.save()
        tags = ['tag1', 'tag2', 'tag3']
        data = _new_document_data(tags)
        response = self.client.post(reverse('wiki.new_revision',
                                    args=[self.d.slug]), data)
        eq_(302, response.status_code)
        eq_(2, self.d.revisions.count())

        new_rev = self.d.revisions.order_by('-id')[0]
        eq_(rev, new_rev.based_on)

    def test_new_revision_POST_removes_old_tags(self):
        """Changing the tags on a document removes the old tags from
        that document."""
        self.d.current_revision = None
        self.d.save()
        tags = ['tag1', 'tag2', 'tag3']
        self.d.tags.add(*tags)
        eq_(tags, list(self.d.tags.values_list('name', flat=True)))
        tags = ['tag1', 'tag4']
        data = _new_document_data(tags)
        self.client.post(reverse('wiki.new_revision', args=[self.d.slug]),
                         data)
        eq_(tags, list(self.d.tags.values_list('name', flat=True)))


class DocumentListTests(TestCaseBase):
    """Tests for the All and Category template"""
    fixtures = ['users.json']

    def setUp(self):
        super(DocumentListTests, self).setUp()
        self.locale = settings.WIKI_DEFAULT_LANGUAGE
        self.doc = _create_document(locale=self.locale)
        _create_document(locale=self.locale, title='Another one')

        # Create a document in different locale to make sure it doesn't show
        _create_document(parent=self.doc, locale='es')
        

    def test_category_list(self):
        """Verify the category documents list view."""
        response = self.client.get(reverse('wiki.category',
                                   args=[self.doc.category]))
        doc = pq(response.content)
        cat = self.doc.category
        eq_(Document.objects.filter(category=cat, locale=self.locale).count(),
            len(doc('#document-list li')))

    def test_all_list(self):
        """Verify the all documents list view."""
        response = self.client.get(reverse('wiki.all_documents'))
        doc = pq(response.content)
        eq_(Document.objects.filter(locale=self.locale).count(),
            len(doc('#document-list li')))


class DocumentRevisionsTests(TestCaseBase):
    """Tests for the Document Revisions template"""
    fixtures = ['users.json']

    def test_document_revisions_list(self):
        """Verify the document revisions list view."""
        d = _create_document()
        user = User.objects.get(pk=118533)
        r1 = revision(summary="a tweak", content='lorem ipsum dolor',
                      significance=SIGNIFICANCES[0][0], keywords='kw1 kw2',
                      document=d, creator=user)
        r1.save()
        r2 = revision(summary="another tweak", content='lorem dimsum dolor',
                      significance=SIGNIFICANCES[0][0], keywords='kw1 kw2',
                      document=d, creator=user)
        r2.save()
        response = self.client.get(reverse('wiki.document_revisions',
                                   args=[d.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(3, len(doc('#revision-list li')))


class ReviewRevisionTests(TestCaseBase):
    """Tests for Review Revisions"""
    fixtures = ['users.json']

    def setUp(self):
        super(ReviewRevisionTests, self).setUp()
        self.document = _create_document()
        user = User.objects.get(pk=118533)
        self.revision = Revision(summary="lipsum",
                                 content='<div>Lorem {for mac}Ipsum{/for} '
                                         'Dolor</div>',
                                 significance=SIGNIFICANCES[0][0],
                                 keywords='kw1 kw2', document=self.document,
                                 creator=user)
        self.revision.save()

        self.client.login(username='admin', password='testpass')

    def test_fancy_renderer(self):
        """Make sure it renders the whizzy new wiki syntax."""
        # The right branch of the template renders only when there's no current
        # revision.
        self.document.current_revision = None
        self.document.save()

        response = get(self.client, 'wiki.review_revision',
                       args=[self.document.slug, self.revision.id])
        self.assertContains(response,
                            '<span data-for="mac" class="for">Ipsum</span>')

    def test_approve_revision(self):
        """Verify revision approval."""
        significance = SIGNIFICANCES[0][0]
        response = post(self.client, 'wiki.review_revision',
                        {'approve': 'Approve Revision',
                         'significance': significance},
                        args=[self.document.slug, self.revision.id])
        eq_(200, response.status_code)
        r = Revision.uncached.get(pk=self.revision.id)
        eq_(significance, r.significance)
        assert r.reviewed
        assert r.is_approved

    def test_reject_revision(self):
        """Verify revision rejection."""
        comment = 'no good'
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision',
                         'comment': comment},
                        args=[self.document.slug, self.revision.id])
        eq_(200, response.status_code)
        r = Revision.uncached.get(pk=self.revision.id)
        eq_(comment, r.comment)
        assert r.reviewed
        assert not r.is_approved

    def test_review_without_permission(self):
        """Make sure unauthorized users can't review revisions."""
        self.client.login(username='rrosario', password='testpass')
        response = post(self.client, 'wiki.review_revision',
                        {'reject': 'Reject Revision'},
                        args=[self.document.slug, self.revision.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/tiki-login.php?next=/en-US/kb/'
            'test-document/review/' + str(self.revision.id),
            redirect[0])


class CompareRevisionTests(TestCaseBase):
    """Tests for Review Revisions"""
    fixtures = ['users.json']

    def setUp(self):
        super(CompareRevisionTests, self).setUp()
        self.document = _create_document()
        self.revision1 = self.document.current_revision
        user = User.objects.get(pk=118533)
        self.revision2 = Revision(summary="lipsum",
                                 content='<div>Lorem Ipsum Dolor</div>',
                                 significance=10, keywords='kw1 kw2',
                                 document=self.document, creator=user)
        self.revision2.save()

        self.client.login(username='admin', password='testpass')

    def test_compare_revisions(self):
        """Compare two revisions"""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': self.revision1.id, 'to': self.revision2.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Dolor',  doc('#revision-diff span.diff_add').text())

    def test_compare_revisions_missing_query_param(self):
        """Try to compare two revisions, with a missing query string param."""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': self.revision1.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'to': self.revision1.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)


class TranslateTests(TestCaseBase):
    """Tests for the Translate page"""
    fixtures = ['users.json']

    def setUp(self):
        super(TranslateTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def test_translate_GET_without_perm(self):
        """Try to create a translation without permission."""
        self.client.login(username='rrosario', password='testpass')
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        eq_(302, response.status_code)

    def test_translate_GET_with_perm(self):
        """HTTP GET to translate URL renders the form."""
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('form textarea[name="content"]')))

    def test_first_translation_to_locale(self):
        """Create the first translation of a doc to new locale."""
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        data = _translation_data()
        response = self.client.post(url, data)
        eq_(302, response.status_code)
        new_doc = Document.objects.get(slug=data['slug'])
        eq_('es', new_doc.locale)
        eq_(data['title'], new_doc.title)
        eq_(self.d, new_doc.parent)
        rev = new_doc.revisions.all()[0]
        eq_(data['keywords'], rev.keywords)
        eq_(data['summary'], rev.summary)
        eq_(data['content'], rev.content)

    def test_another_translation_to_locale(self):
        """Create the second translation of a doc."""
        # First create the first one with test above
        self.test_first_translation_to_locale()
        # Approve the translation
        rev_es = Revision.objects.filter(document__locale='es')[0]
        rev_es.is_approved = True
        rev_es.save()

        # Create and approve a new en-US revision
        rev_enUS = Revision(summary="lipsum",
                       content='lorem ipsum dolor sit amet new',
                       significance=10, keywords='kw1 kw2',
                       document=self.d, creator_id=118577, is_approved=True)
        rev_enUS.save()

        # Verify the form renders with correct content
        url = reverse('wiki.translate', locale='es', args=[self.d.slug])
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(rev_es.content, doc('#id_content').text())
        eq_(rev_enUS.content, doc('#content-fields textarea[readonly]').text())

        # Post the translation and verify
        data = _translation_data()
        data['content'] = 'loremo ipsumo doloro sito ameto nuevo'
        response = self.client.post(url, data)
        doc = Document.objects.get(slug=data['slug'])
        rev = doc.revisions.filter(content=data['content'])[0]
        eq_(data['keywords'], rev.keywords)
        eq_(data['summary'], rev.summary)
        eq_(data['content'], rev.content)
        assert not rev.is_approved


def _create_document(title='Test Document', parent=None,
                     locale=settings.WIKI_DEFAULT_LANGUAGE):
    d = document(title=title, html='<div>Lorem Ipsum</div>',
                 category=1, locale=locale, parent=parent)
    d.save()
    r = Revision(document=d, keywords='key1, key2', summary='lipsum',
                 content='<div>Lorem Ipsum</div>', creator_id=118577,
                 significance=SIGNIFICANCES[0][0])
    r.save()
    d.current_revision = r
    d.save()
    return d


def _new_document_data(tags):
    return {
        'title': 'A Test Article',
        'slug': 'a-test-article',
        'tags': ','.join(tags),
        'firefox_versions': [1, 2],
        'operating_systems': [1, 3],
        'category': CATEGORIES[0][0],
        'keywords': 'key1, key2',
        'summary': 'lipsum',
        'content': 'lorem ipsum dolor sit amet',
        'significance': SIGNIFICANCES[0][0],
    }


def _translation_data():
    return {
        'title': 'Un Test Articulo', 'slug': 'un-test-articulo',
        'category': CATEGORIES[0][0],
        'tags': 'tagUno,tagDos,tagTres',
        'keywords': 'keyUno, keyDos, keyTres',
        'summary': 'lipsumo',
        'content': 'loremo ipsumo doloro sito ameto',
        'significance': SIGNIFICANCES[0][0]}


def _verify_doc_and_rev_data(data, doc, rev):
    """Verify that the Document and Revision match the data."""
    eq_(data['title'], doc.title)
    eq_(data['category'], doc.category)
    eq_(data['summary'], rev.summary)
    eq_(data['keywords'], rev.keywords)
    eq_(data['content'], rev.content)
