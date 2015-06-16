# -*- coding: utf-8 -*-
from datetime import datetime
import time
import urllib

from BeautifulSoup import BeautifulSoup
import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.utils.http import urlquote
from django.test.utils import override_settings

from constance import config
from jingo.helpers import urlparams
from waffle.models import Flag

from kuma.core.tests import SkippedTestCase, post, get
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase
from ..events import EditDocumentEvent
from ..constants import REDIRECT_CONTENT, TEMPLATE_TITLE_PREFIX
from ..models import Document, Revision, HelpfulVote, DocumentTag
from . import (WikiTestCase, document, revision, new_document_data,
               create_topical_parents_docs)


DOCUMENT_EDITED_EMAIL_CONTENT = """


admin created a new revision to the document
%s.

To view this document's history, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/docs/%s$history
"""


class DocumentTests(UserTestCase, WikiTestCase):
    """Tests for the Document template"""

    def test_document_view(self):
        """Load the document view page and verify the title and content."""
        r = revision(save=True, content='Some text.', is_approved=True)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(r.document.title, doc('main#content div.document-head h1').text())
        eq_(r.document.html, doc('article#wikiArticle').text())

    def test_custom_css_waffle(self):
        """
        Verify KUMA_CUSTOM_CSS_PATH is only included when waffle flag is
        active.
        """
        r = revision(save=True, content='Some text.', is_approved=True)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        ok_(config.KUMA_CUSTOM_CSS_PATH not in response.content)

        Flag.objects.create(name='enable_customcss', everyone=True)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        ok_(config.KUMA_CUSTOM_CSS_PATH in response.content)

    @attr("breadcrumbs")
    def test_document_breadcrumbs(self):
        """Create docs with topical parent/child rel, verify breadcrumbs."""
        d1, d2 = create_topical_parents_docs()
        response = self.client.get(d1.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(d1.title, doc('main#content div.document-head h1').text())
        eq_(d1.title, doc('nav.crumbs li:last-child').text())
        response = self.client.get(d2.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(d2.title, doc('main#content div.document-head h1').text())
        crumbs = "MDN %s %s" % (d1.title, d2.title)
        eq_(crumbs, doc('nav.crumbs').text())

    def test_english_document_no_approved_content(self):
        """Load an English document with no approved content."""
        r = revision(save=True, content='Some text.', is_approved=False)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(r.document.title, doc('main#content div.document-head h1').text())
        eq_("This article doesn't have approved content yet.",
            doc('article#wikiArticle').text())

    def test_translation_document_no_approved_content(self):
        """Load a non-English document with no approved content, with a parent
        with no approved content either."""
        r = revision(save=True, content='Some text.', is_approved=False)
        d2 = document(parent=r.document, locale='fr', slug='french', save=True)
        revision(document=d2, save=True, content='Moartext', is_approved=False)
        response = self.client.get(d2.get_absolute_url())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(d2.title, doc('main#content div.document-head h1').text())
        # HACK: fr doc has different message if locale/ is updated
        ok_(
            ("This article doesn't have approved content yet." in
                doc('article#wikiArticle').text())
            or
            ("Cet article n'a pas encore de contenu" in
                doc('article#wikiArticle').text()))

    def test_document_fallback_with_translation(self):
        """The document template falls back to English if translation exists
        but it has no approved revisions."""
        r = revision(save=True, content='Test', is_approved=True)
        d2 = document(parent=r.document, locale='fr', slug='french', save=True)
        revision(document=d2, is_approved=False, save=True)
        url = reverse('wiki.document', args=[d2.slug], locale='fr')
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(d2.title, doc('main#content div.document-head h1').text())

        # Fallback message is shown.
        eq_(1, len(doc('#doc-pending-fallback')))
        ok_('$translate' in doc('#edit-button').attr('href'))
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        eq_(pq(r.document.html).text(), doc('article#wikiArticle').text())

    def test_document_fallback_no_translation(self):
        """The document template falls back to English if no translation
        exists."""
        r = revision(save=True, content='Some text.', is_approved=True)
        url = reverse('wiki.document', args=[r.document.slug], locale='fr')
        response = self.client.get(url)
        doc = pq(response.content)
        eq_(r.document.title, doc('main#content div.document-head h1').text())

        # Fallback message is shown.
        eq_(1, len(doc('#doc-pending-fallback')))
        ok_('$translate' in doc('#edit-button').attr('href'))
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        eq_(pq(r.document.html).text(), doc('article#wikiArticle').text())

    def test_redirect(self):
        """Make sure documents with REDIRECT directives redirect properly.

        Also check the backlink to the redirect page.
        """
        Flag.objects.create(name='redirect_messages', everyone=True)
        target = document(save=True)
        target_url = target.get_absolute_url()

        # Ordinarily, a document with no approved revisions cannot have HTML,
        # but we shove it in manually here as a shortcut:
        redirect_html = REDIRECT_CONTENT % dict(title='Boo', href=target_url)
        redirect = document(html=redirect_html)
        redirect.save()
        redirect_url = redirect.get_absolute_url()
        response = self.client.get(redirect_url)
        response = self.client.get(redirect_url, follow=True)
        self.assertRedirects(response, urlparams(target_url), status_code=301)
        self.assertContains(response, redirect_url)

    def test_redirect_from_nonexistent(self):
        """The template shouldn't crash or print a backlink if the "from" page
        doesn't exist."""
        d = document(save=True)
        response = self.client.get(urlparams(d.get_absolute_url()))
        self.assertNotContains(response, 'Redirected from ')

    def test_watch_includes_csrf(self):
        """The watch/unwatch forms should include the csrf tag."""
        self.client.login(username='testuser', password='testpass')
        d = document(save=True)
        resp = self.client.get(d.get_absolute_url())
        doc = pq(resp.content)
        assert doc('.page-watch input[type=hidden]')

    def test_non_localizable_translate_disabled(self):
        """Non localizable document doesn't show tab for 'Localize'."""
        self.client.login(username='testuser', password='testpass')
        d = document(is_localizable=True, save=True)
        resp = self.client.get(d.get_absolute_url())
        doc = pq(resp.content)
        assert 'Add a translation' in doc('.page-buttons #translations li').text()

        # Make it non-localizable
        d.is_localizable = False
        d.save()
        resp = self.client.get(d.get_absolute_url())
        doc = pq(resp.content)
        assert 'Add a translation' not in doc('.page-buttons #translations li').text()

    @attr('toc')
    def test_toc_depth(self):
        """Toggling show_toc on/off through the toc_depth field should
        cause table of contents to appear/disappear."""
        doc_content = """
        <h2>This is a section</h2>
        <p>This is section content.</p>
        <h2>This is another section</h2>
        <p>This is more section content.</p>
        """
        r = revision(save=True, content=doc_content, is_approved=True)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        ok_('<div id="toc"' in response.content)
        new_r = revision(document=r.document, content=r.content,
                         toc_depth=0, is_approved=True)
        new_r.save()
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        ok_('<div class="page-toc">' not in response.content)

    @attr('toc')
    def test_show_toc_hidden_input_for_templates(self):
        """Toggling show_toc on/off through the toc_depth field should
        cause table of contents to appear/disappear."""
        doc_content = """w00t"""
        doc = document(slug="Template:w00t", save=True)
        r = revision(document=doc, save=True, content=doc_content,
                     is_approved=True)
        response = self.client.get(r.document.get_absolute_url())
        eq_(200, response.status_code)
        soup = BeautifulSoup(response.content)
        hidden_inputs = soup.findAll("input", type="hidden")
        for input in hidden_inputs:
            if input['name'] == 'toc_depth':
                eq_(0, input['value'])


class RevisionTests(UserTestCase, WikiTestCase):
    """Tests for the Revision template"""
    localizing_client = True

    def test_revision_view(self):
        """Load the revision view page and verify the title and content."""
        d = _create_document()
        r = d.current_revision
        r.created = datetime(2011, 1, 1)
        r.save()
        url = reverse('wiki.revision', args=[d.slug, r.id])
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Revision id: %s' % r.id,
            doc('div.revision-info li.revision-id').text())
        eq_('Revision %s of %s' % (r.id, d.title), doc('h1').text())
        eq_(r.content,
            doc('#doc-source pre').text())
        eq_('Created: Jan 1, 2011, 12:00:00 AM',
            doc('div.revision-info li.revision-created').text().strip())


class NewDocumentTests(UserTestCase, WikiTestCase):
    """Tests for the New Document template"""
    localizing_client = True

    def test_new_document_GET_with_perm(self):
        """HTTP GET to new document URL renders the form."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('form#wiki-page-edit input[name="title"]')))

    @attr('bug1052047')
    def test_new_document_includes_review_block(self):
        """
        New document page includes 'Review Needed?' section.
        https://bugzil.la/1052047
        """
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))

        test_strings = ['Review needed?', 'Technical', 'Editorial']
        eq_(200, response.status_code)

        # TODO: push test_strings functionality up into a test helper
        for test_string in test_strings:
            ok_(test_string in response.content)

    def test_new_document_preview_button(self):
        """HTTP GET to new document URL shows preview button for basic doc
        and not for template doc"""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        eq_(200, response.status_code)
        doc = pq(response.content)
        ok_(len(doc('.btn-preview')) > 0)

        response = self.client.get(reverse('wiki.new_document') +
                                   '?slug=' + TEMPLATE_TITLE_PREFIX)
        doc = pq(response.content)
        eq_(0, len(doc('.btn-preview')))

    def test_new_document_form_defaults(self):
        """The new document form should have all all 'Relevant to' options
        checked by default."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.new_document'))
        doc = pq(response.content)
        eq_("Name Your Article", doc('input#id_title').attr('placeholder'))
        eq_("10", doc('input#id_category').attr('value'))

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_document_POST(self, get_current):
        """HTTP POST to new document URL creates the document."""
        get_current.return_value.domain = 'testserver'

        self.client.login(username='admin', password='testpass')
        tags = ['tag1', 'tag2']
        data = new_document_data(tags)
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        d = Document.objects.get(title=data['title'])
        eq_([('http://testserver/en-US/docs/%s' % d.slug, 302)],
            response.redirect_chain)
        eq_(settings.WIKI_DEFAULT_LANGUAGE, d.locale)
        eq_(data['category'], d.category)
        eq_(tags, sorted(t.name for t in d.tags.all()))
        r = d.revisions.all()[0]
        eq_(data['keywords'], r.keywords)
        eq_(data['summary'], r.summary)
        eq_(data['content'], r.content)

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_document_other_locale(self, get_current):
        """Make sure we can create a document in a non-default locale."""
        # You shouldn't be able to make a new doc in a non-default locale
        # without marking it as non-localizable. Unskip this when the non-
        # localizable bool is implemented.
        get_current.return_value.domain = 'testserver'

        self.client.login(username='admin', password='testpass')
        data = new_document_data(['tag1', 'tag2'])
        locale = 'es'
        self.client.post(reverse('wiki.new_document', locale=locale),
                         data, follow=True)
        d = Document.objects.get(title=data['title'])
        eq_(locale, d.locale)

    def test_new_document_POST_empty_title(self):
        """Trigger required field validation for title."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data(['tag1', 'tag2'])
        data['title'] = ''
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('article > ul.errorlist')
        ok_(len(ul) > 0)
        ok_('Please provide a title.' in ul('li').text())

    def test_new_document_POST_empty_content(self):
        """Trigger required field validation for content."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data(['tag1', 'tag2'])
        data['content'] = ''
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('article > ul.errorlist')
        eq_(1, len(ul))
        eq_('Please provide content.', ul('li').text())

    def test_new_document_POST_invalid_category(self):
        """Try to create a new document with an invalid category value."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data(['tag1', 'tag2'])
        data['category'] = 963
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        doc = pq(response.content)
        ul = doc('article > ul.errorlist')
        eq_(1, len(ul))
        assert ('Select a valid choice. 963 is not one of the available '
                'choices.' in ul('li').text())

    def test_new_document_missing_category(self):
        """Test the DocumentForm's category validation.

        Submit the form without a category set, and it should complain, even
        though it's not a strictly required field (because it cannot be set for
        translations).

        """
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        del data['category']
        response = self.client.post(reverse('wiki.new_document'), data,
                                    follow=True)
        self.assertContains(response, 'Please choose a category.')

    def test_slug_collision_validation(self):
        """Trying to create document with existing locale/slug should
        show validation error."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = d.slug
        response = self.client.post(reverse('wiki.new_document'), data)
        eq_(200, response.status_code)
        doc = pq(response.content)
        ul = doc('article > ul.errorlist')
        eq_(1, len(ul))
        eq_('Document with this Slug and Locale already exists.',
            ul('li').text())

    def test_title_no_collision(self):
        """Only slugs and not titles are required to be unique per
        locale now, so test that we actually allow that."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = '%s-once-more-with-feeling' % d.slug
        response = self.client.post(reverse('wiki.new_document'), data)
        eq_(302, response.status_code)

    def test_slug_3_chars(self):
        """Make sure we can create a slug with only 3 characters."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = 'ask'
        response = self.client.post(reverse('wiki.new_document'), data)
        eq_(302, response.status_code)
        eq_('ask', Document.objects.all()[0].slug)


class NewRevisionTests(UserTestCase, WikiTestCase):
    """Tests for the New Revision template"""
    localizing_client = True

    def setUp(self):
        super(NewRevisionTests, self).setUp()
        self.d = _create_document()
        self.username = 'admin'
        self.client.login(username=self.username, password='testpass')

    def test_new_revision_GET_logged_out(self):
        """Creating a revision without being logged in redirects to login page.
        """
        self.client.logout()
        response = self.client.get(reverse('wiki.edit_document',
                                           args=[self.d.slug]))
        eq_(302, response.status_code)

    def test_new_revision_GET_with_perm(self):
        """HTTP GET to new revision URL renders the form."""
        response = self.client.get(reverse('wiki.edit_document',
                                           args=[self.d.slug]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('article#edit-document '
                       'form#wiki-page-edit textarea[name="content"]')))

    def test_new_revision_GET_based_on(self):
        """HTTP GET to new revision URL based on another revision.

        This case should render the form with the fields pre-populated
        with the based-on revision info.

        """
        r = Revision(document=self.d, keywords='ky1, kw2',
                     summary='the summary',
                     content='<div>The content here</div>', creator_id=7)
        r.save()
        response = self.client.get(reverse('wiki.new_revision_based_on',
                                           args=[self.d.slug, r.id]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        self.assertHTMLEqual(doc('#id_content')[0].value.strip(),
                             r.content.strip())

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @mock.patch.object(Site.objects, 'get_current')
    @mock.patch.object(settings._wrapped, 'TIDINGS_CONFIRM_ANONYMOUS_WATCHES', False)
    def test_new_revision_POST_document_with_current(self, get_current):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case already has a current_revision, therefore
        the document document fields are not editable.

        Also assert that the edited and reviewable notifications go out.

        """
        get_current.return_value.domain = 'testserver'

        # Sign up for notifications:
        EditDocumentEvent.notify('sam@example.com', self.d).activate().save()

        # Edit a document (pause for get_previous)
        time.sleep(1)
        response = self.client.post(
            reverse('wiki.edit_document', args=[self.d.slug]),
            {'summary': 'A brief summary', 'content': 'The article content',
             'keywords': 'keyword1 keyword2', 'slug': self.d.slug, 'toc_depth': 1,
             'based_on': self.d.current_revision.id, 'form': 'rev'})
        ok_(response.status_code in (200, 302))
        eq_(2, self.d.revisions.count())
        new_rev = self.d.revisions.order_by('-id')[0]
        eq_(self.d.current_revision, new_rev.based_on)

        # Assert notifications fired and have the expected content:
        # 1 email for the first time edit notification
        # 1 email for the EditDocumentEvent to sam@example.com
        # Regression check:
        # messing with context processors can
        # cause notification emails to error
        # and stop being sent.
        eq_(2, len(mail.outbox))
        first_edit_email = mail.outbox[0]
        expected_to = [config.EMAIL_LIST_FOR_FIRST_EDITS]
        expected_subject = u'[MDN] %(username)s made their first edit, to: %(title)s' % ({'username': new_rev.creator.username, 'title': self.d.title})
        eq_(expected_subject, first_edit_email.subject)
        eq_(expected_to, first_edit_email.to)

        edited_email = mail.outbox[1]
        expected_to = [u'sam@example.com']
        expected_subject = u'[MDN] Page "%s" changed by %s' % (self.d.title,
                                                               new_rev.creator)
        eq_(expected_subject, edited_email.subject)
        eq_(expected_to, edited_email.to)
        ok_('%s changed %s.' % (unicode(self.username), unicode(self.d.title))
            in edited_email.body)
        ok_(u'https://testserver/en-US/docs/%s$history?utm_campaign=' %
            self.d.slug
            in edited_email.body)

    @mock.patch.object(EditDocumentEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_new_revision_POST_document_without_current(
            self, get_current, edited_fire):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case doesn't have a current_revision, therefore
        the document fields are open for editing.

        """
        get_current.return_value.domain = 'testserver'

        self.d.current_revision = None
        self.d.save()
        tags = ['tag1', 'tag2', 'tag3']
        data = new_document_data(tags)
        data['form'] = 'rev'
        response = self.client.post(reverse('wiki.edit_document',
                                    args=[self.d.slug]), data)
        eq_(302, response.status_code)
        eq_(2, self.d.revisions.count())

        new_rev = self.d.revisions.order_by('-id')[0]
        # There are no approved revisions, so it's based_on nothing:
        eq_(None, new_rev.based_on)
        edited_fire.assert_called()

    def test_new_revision_POST_removes_old_tags(self):
        """Changing the tags on a document removes the old tags from
        that document."""
        self.d.current_revision = None
        self.d.save()
        tags = [u'tag1', u'tag2', u'tag3']
        self.d.tags.add(*tags)
        result_tags = list(self.d.tags.values_list('name', flat=True))
        result_tags.sort()
        eq_(tags, result_tags)
        tags = [u'tag1', u'tag4']
        data = new_document_data(tags)
        data['form'] = 'rev'
        self.client.post(reverse('wiki.edit_document',
                                 args=[self.d.slug]),
                         data)
        result_tags = list(self.d.tags.values_list('name', flat=True))
        result_tags.sort()
        eq_(tags, result_tags)

    def test_new_form_maintains_based_on_rev(self):
        """Revision.based_on should be the rev that was current when the Edit
        button was clicked, even if other revisions happen while the user is
        editing."""
        _test_form_maintains_based_on_rev(
            self.client, self.d, 'wiki.edit_document',
            {'summary': 'Windy', 'content': 'gerbils', 'form': 'rev',
             'slug': self.d.slug, 'toc_depth': 1},
            locale='en-US')


class DocumentEditTests(UserTestCase, WikiTestCase):
    """Test the editing of document level fields."""
    localizing_client = True

    def setUp(self):
        super(DocumentEditTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def test_can_save_document_with_translations(self):
        """Make sure we can save a document with translations."""
        # Create a translation
        _create_document(title='Document Prueba', parent=self.d,
                         locale='es')
        # Make sure is_localizable hidden field is rendered
        response = get(self.client, 'wiki.edit_document',
                       args=[self.d.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        data = new_document_data()
        new_title = 'A brand new title'
        data.update(title=new_title)
        data.update(form='doc')
        data.update(is_localizable='True')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        eq_(new_title, doc.title)

    def test_change_slug_case(self):
        """Changing the case of some letters in the slug should work."""
        data = new_document_data()
        new_slug = 'Test-Document'
        data.update(slug=new_slug)
        data.update(form='doc')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        eq_(new_slug, doc.slug)

    def test_change_title_case(self):
        """Changing the case of some letters in the title should work."""
        data = new_document_data()
        new_title = 'TeST DoCuMent'
        data.update(title=new_title)
        data.update(form='doc')
        response = post(self.client, 'wiki.edit_document', data,
                        args=[self.d.slug])
        eq_(200, response.status_code)
        doc = Document.objects.get(pk=self.d.pk)
        eq_(new_title, doc.title)


class DocumentListTests(UserTestCase, WikiTestCase):
    """Tests for the All and Category template"""
    localizing_client = True

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
            len(doc('#document-list ul.document-list li')))

    def test_all_list(self):
        """Verify the all documents list view."""
        response = self.client.get(reverse('wiki.all_documents'))
        doc = pq(response.content)
        eq_(Document.objects.filter(locale=self.locale).count(),
            len(doc('#document-list ul.document-list li')))

    @attr('tags')
    def test_tag_list(self):
        """Verify the tagged documents list view."""
        tag = DocumentTag(name='Test Tag', slug='test-tag')
        tag.save()
        self.doc.tags.add(tag)
        response = self.client.get(reverse('wiki.tag',
                                   args=[tag.name]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#document-list ul.document-list li')))

    # http://bugzil.la/871638
    @attr('tags')
    def test_tag_list_duplicates(self):
        """
        Verify the tagged documents list view, even for duplicate tags
        """
        en_tag = DocumentTag(name='CSS Reference', slug='css-reference')
        en_tag.save()
        fr_tag = DocumentTag(name=u'CSS Référence', slug='css-reference_1')
        fr_tag.save()
        self.doc.tags.add(en_tag)
        self.doc.tags.add(fr_tag)
        response = self.client.get(reverse('wiki.tag',
                                   args=[en_tag.name]))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#document-list ul.document-list li')))


class CompareRevisionTests(UserTestCase, WikiTestCase):
    """Tests for Review Revisions"""
    localizing_client = True

    def setUp(self):
        super(CompareRevisionTests, self).setUp()
        self.document = _create_document()
        self.revision1 = self.document.current_revision
        user = self.user_model.objects.get(username='testuser')
        self.revision2 = Revision(summary="lipsum",
                                  content='<div>Lorem Ipsum Dolor</div>',
                                  keywords='kw1 kw2',
                                  document=self.document, creator=user)
        self.revision2.save()

        self.client.login(username='admin', password='testpass')

    def test_bad_parameters(self):
        """Ensure badly-formed revision parameters do not cause errors"""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': '1e309', 'to': u'1e309'}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

    def test_compare_revisions(self):
        """Compare two revisions"""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': self.revision1.id, 'to': self.revision2.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Dolor', doc('span.diff_add').text())

    def test_compare_revisions_invalid_to_int(self):
        """Provide invalid 'to' int for revision ids."""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': '', 'to': 'invalid'}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

    def test_compare_revisions_invalid_from_int(self):
        """Provide invalid 'from' int for revision ids."""
        url = reverse('wiki.compare_revisions', args=[self.document.slug])
        query = {'from': 'invalid', 'to': ''}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)

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

    def test_compare_unmatched_document_url(self):
        """Comparing two revisions of unlinked document should cause error."""
        unmatched_document = _create_document(title='Invalid document')
        url = reverse('wiki.compare_revisions', args=[unmatched_document.slug])
        query = {'from': self.revision1.id, 'to': self.revision2.id}
        url = urlparams(url, **query)
        response = self.client.get(url)
        eq_(404, response.status_code)


class TranslateTests(UserTestCase, WikiTestCase):
    """Tests for the Translate page"""

    def setUp(self):
        super(TranslateTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def _translate_uri(self):
        translate_path = self.d.slug
        translate_uri = reverse('wiki.translate',
                                locale='en-US',
                                args=[translate_path])
        return '%s?tolocale=%s' % (translate_uri, 'es')

    def test_translate_GET_logged_out(self):
        """Try to create a translation while logged out."""
        self.client.logout()
        translate_uri = self._translate_uri()
        response = self.client.get(translate_uri)
        eq_(302, response.status_code)
        expected_url = '%s?next=%s' % (reverse('account_login', locale='en-US'),
                                       urlquote(translate_uri))
        ok_(expected_url in response['Location'])

    def test_translate_GET_with_perm(self):
        """HTTP GET to translate URL renders the form."""
        response = self.client.get(self._translate_uri())
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('form textarea[name="content"]')))
        # initial translation should include slug input
        eq_(1, len(doc('form input[name="slug"]')))
        assert (u'Espa' in doc('div.change-locale').text())

    def test_translate_disallow(self):
        """HTTP GET to translate URL returns 400 when not localizable."""
        self.d.is_localizable = False
        self.d.save()
        response = self.client.get(self._translate_uri())
        eq_(400, response.status_code)

    def test_invalid_document_form(self):
        """Make sure we handle invalid document form without a 500."""
        translate_uri = self._translate_uri()
        data = _translation_data()
        data['slug'] = ''  # Invalid slug
        response = self.client.post(translate_uri, data)
        eq_(200, response.status_code)

    def test_invalid_revision_form(self):
        """When creating a new translation, an invalid revision form shouldn't
        result in a new Document being created."""
        translate_uri = self._translate_uri()
        data = _translation_data()
        data['content'] = ''  # Content is required
        response = self.client.post(translate_uri, data)
        eq_(200, response.status_code)
        eq_(0, self.d.translations.count())

    @mock.patch.object(EditDocumentEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_first_translation_to_locale(self, get_current, edited_fire):
        """Create the first translation of a doc to new locale."""
        get_current.return_value.domain = 'testserver'

        translate_uri = self._translate_uri()
        data = _translation_data()
        response = self.client.post(translate_uri, data)
        eq_(302, response.status_code)
        new_doc = Document.objects.get(slug=data['slug'])
        eq_('es', new_doc.locale)
        eq_(data['title'], new_doc.title)
        eq_(self.d, new_doc.parent)
        rev = new_doc.revisions.all()[0]
        eq_(data['keywords'], rev.keywords)
        eq_(data['summary'], rev.summary)
        eq_(data['content'], rev.content)
        edited_fire.assert_called()

    def _create_and_approve_first_translation(self):
        """Returns the revision."""
        # First create the first one with test above
        self.test_first_translation_to_locale()
        # Approve the translation
        rev_es = Revision.objects.filter(document__locale='es')[0]
        rev_es.is_approved = True
        rev_es.save()
        return rev_es

    @mock.patch.object(EditDocumentEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_another_translation_to_locale(self, get_current, edited_fire):
        """Create the second translation of a doc."""
        get_current.return_value.domain = 'testserver'

        rev_es = self._create_and_approve_first_translation()

        # Create and approve a new en-US revision
        rev_enUS = Revision(summary="lipsum",
                            content='lorem ipsum dolor sit amet new',
                            keywords='kw1 kw2',
                            document=self.d, creator_id=8, is_approved=True)
        rev_enUS.save()

        # Verify the form renders with correct content
        translate_uri = self._translate_uri()
        response = self.client.get(translate_uri)
        doc = pq(response.content)
        eq_(rev_es.content, doc('#id_content').text())
        eq_(rev_enUS.content, doc('article.approved .translate-rendered').text())

        # Post the translation and verify
        data = _translation_data()
        data['content'] = 'loremo ipsumo doloro sito ameto nuevo'
        response = self.client.post(translate_uri, data)
        eq_(302, response.status_code)
        eq_('http://testserver/es/docs/un-test-articulo',
            response['location'])
        doc = Document.objects.get(slug=data['slug'])
        rev = doc.revisions.filter(content=data['content'])[0]
        eq_(data['keywords'], rev.keywords)
        eq_(data['summary'], rev.summary)
        eq_(data['content'], rev.content)
        edited_fire.assert_called()

        # subsequent translations should NOT include slug input
        self.client.logout()
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(translate_uri)
        doc = pq(response.content)
        eq_(0, len(doc('form input[name="slug"]')))

    def test_translate_form_maintains_based_on_rev(self):
        """Revision.based_on should be the rev that was current when the
        Translate button was clicked, even if other revisions happen while the
        user is editing."""
        raise SkipTest("Figure out WTF is going on with this one.")
        _test_form_maintains_based_on_rev(self.client,
                                          self.d,
                                          'wiki.translate',
                                          _translation_data(),
                                          trans_lang='es',
                                          locale='en-US')

    def test_translate_update_doc_only(self):
        """Submitting the document form should update document. No new
        revisions should be created."""
        rev_es = self._create_and_approve_first_translation()
        translate_uri = self._translate_uri()
        data = _translation_data()
        new_title = 'Un nuevo titulo'
        data['title'] = new_title
        data['form'] = 'doc'
        response = self.client.post(translate_uri, data)
        eq_(302, response.status_code)
        eq_('http://testserver/es/docs/un-test-articulo$edit'
            '?opendescription=1',
            response['location'])
        revisions = rev_es.document.revisions.all()
        eq_(1, revisions.count())  # No new revisions
        d = Document.objects.get(id=rev_es.document.id)
        eq_(new_title, d.title)  # Title is updated

    def test_translate_update_rev_and_doc(self):
        """Submitting the revision form should create a new revision.
        And since Kuma docs default to approved, should update doc too."""
        rev_es = self._create_and_approve_first_translation()
        translate_uri = self._translate_uri()
        data = _translation_data()
        new_title = 'Un nuevo titulo'
        data['title'] = new_title
        data['form'] = 'rev'
        response = self.client.post(translate_uri, data)
        eq_(302, response.status_code)
        eq_('http://testserver/es/docs/un-test-articulo',
            response['location'])
        revisions = rev_es.document.revisions.all()
        eq_(2, revisions.count())  # New revision is created
        d = Document.objects.get(id=rev_es.document.id)
        eq_(data['title'], d.title)  # Title isn't updated

    def test_translate_form_content_fallback(self):
        """If there are existing but unapproved translations, prefill
        content with latest."""
        self.test_first_translation_to_locale()
        translate_uri = self._translate_uri()
        response = self.client.get(translate_uri)
        doc = pq(response.content)
        document = Document.objects.filter(locale='es')[0]
        existing_rev = document.revisions.all()[0]
        eq_(existing_rev.content, doc('#id_content').text())

    def test_translate_based_on(self):
        raise SkipTest("Figure out WTF is going on with this one.")
        """Test translating based on a non-current revision."""
        # Create the base revision
        base_rev = self._create_and_approve_first_translation()
        # Create a new current revision
        r = revision(document=base_rev.document, is_approved=True)
        r.save()
        d = Document.objects.get(pk=base_rev.document.id)
        eq_(r, base_rev.document.current_revision)

        uri = reverse('wiki.new_revision_based_on',
                      locale=d.locale,
                      args=[d.slug, base_rev.id])
        response = self.client.get(uri)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(doc('#id_content')[0].value, base_rev.content)


def _test_form_maintains_based_on_rev(client, doc, view, post_data,
                                      trans_lang=None, locale=None):
    """Confirm that the based_on value set in the revision created by an edit
    or translate form is the current_revision of the document as of when the
    form was first loaded, even if other revisions have been approved in the
    meantime."""
    if trans_lang:
        translate_path = doc.slug
        uri = urllib.quote(reverse('wiki.translate',
                                   locale=trans_lang,
                                   args=[translate_path]))
    else:
        uri = reverse(view, locale=locale, args=[doc.slug])
    response = client.get(uri)
    orig_rev = doc.current_revision
    eq_(orig_rev.id,
        int(pq(response.content)('input[name=based_on]').attr('value')))

    # While Fred is editing the above, Martha approves a new rev:
    martha_rev = revision(document=doc)
    martha_rev.is_approved = True
    martha_rev.save()

    # Then Fred saves his edit:
    post_data_copy = {'based_on': orig_rev.id, 'slug': orig_rev.slug}
    post_data_copy.update(post_data)  # Don't mutate arg.
    response = client.post(uri,
                           data=post_data_copy)
    ok_(response.status_code in (200, 302))
    fred_rev = Revision.objects.all().order_by('-id')[0]
    eq_(orig_rev, fred_rev.based_on)


class ArticlePreviewTests(UserTestCase, WikiTestCase):
    """Tests for preview view and template."""
    localizing_client = True

    def setUp(self):
        super(ArticlePreviewTests, self).setUp()
        self.client.login(username='testuser', password='testpass')

    def test_preview_GET_405(self):
        """Preview with HTTP GET results in 405."""
        response = get(self.client, 'wiki.preview')
        eq_(405, response.status_code)

    def test_preview(self):
        """Preview the wiki syntax content."""
        response = post(self.client, 'wiki.preview',
                        {'content': '<h1>Test Content</h1>'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Test Content', doc('article#wikiArticle h1').text())

    def test_preview_locale(self):
        raise SkipTest
        """Preview the wiki syntax content."""
        # Create a test document and translation.
        d = _create_document()
        _create_document(title='Prueba', parent=d, locale='es')
        # Preview content that links to it and verify link is in locale.
        url = reverse('wiki.preview', locale='es')
        response = self.client.post(url, {'content': '[[Test Document]]'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        link = doc('#doc-content a')
        eq_('Prueba', link.text())
        eq_('/es/docs/prueba', link[0].attrib['href'])


class HelpfulVoteTests(UserTestCase, SkippedTestCase):

    def setUp(self):
        super(HelpfulVoteTests, self).setUp()
        self.document = _create_document()

    def test_vote_yes(self):
        """Test voting helpful."""
        d = self.document
        user = self.user_model.objects.get(username='testuser')
        self.client.login(username='testuser', password='testpass')
        response = post(self.client, 'wiki.document_vote',
                        {'helpful': 'Yes'}, args=[self.document.slug])
        eq_(200, response.status_code)
        votes = HelpfulVote.objects.filter(document=d, creator=user)
        eq_(1, votes.count())
        assert votes[0].helpful

    def test_vote_no(self):
        """Test voting not helpful."""
        d = self.document
        user = self.user_model.objects.get(username='testuser')
        self.client.login(username='testuser', password='testpass')
        response = post(self.client, 'wiki.document_vote',
                        {'not-helpful': 'No'}, args=[d.slug])
        eq_(200, response.status_code)
        votes = HelpfulVote.objects.filter(document=d, creator=user)
        eq_(1, votes.count())
        assert not votes[0].helpful

    def test_vote_anonymous(self):
        """Test that voting works for anonymous user."""
        d = self.document
        response = post(self.client, 'wiki.document_vote',
                        {'helpful': 'Yes'}, args=[d.slug])
        eq_(200, response.status_code)
        votes = HelpfulVote.objects.filter(document=d, creator=None)
        votes = votes.exclude(anonymous_id=None)
        eq_(1, votes.count())
        assert votes[0].helpful

    def test_vote_ajax(self):
        """Test voting via ajax."""
        d = self.document
        url = reverse('wiki.document_vote', args=[d.slug])
        response = self.client.post(url, data={'helpful': 'Yes'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(200, response.status_code)
        eq_('{"message": "Glad to hear it &mdash; thanks for the feedback!"}',
            response.content)
        votes = HelpfulVote.objects.filter(document=d, creator=None)
        votes = votes.exclude(anonymous_id=None)
        eq_(1, votes.count())
        assert votes[0].helpful


class SelectLocaleTests(UserTestCase, WikiTestCase):
    """Test the locale selection page"""

    def setUp(self):
        super(SelectLocaleTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def test_page_renders_locales(self):
        """Load the page and verify it contains all the locales for l10n."""
        response = get(self.client, 'wiki.select_locale',
                       args=[self.d.slug])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(len(settings.LANGUAGES) - 1,  # All except for 1 (en-US)
            len(doc('#select-locale ul.locales li')))


class RevisionDeleteTestCase(UserTestCase, SkippedTestCase):

    def setUp(self):
        super(RevisionDeleteTestCase, self).setUp()
        self.d = _create_document()
        self.r = revision(document=self.d)
        self.r.save()

    def test_delete_revision_without_permissions(self):
        """Deleting a revision without permissions sends 403."""
        self.client.login(username='testuser', password='testpass')
        response = get(self.client, 'wiki.delete_revision',
                       args=[self.d.slug, self.r.id])
        eq_(403, response.status_code)

        response = post(self.client, 'wiki.delete_revision',
                        args=[self.d.slug, self.r.id])
        eq_(403, response.status_code)

    def test_delete_revision_logged_out(self):
        """Deleting a revision while logged out redirects to login."""
        response = get(self.client, 'wiki.delete_revision',
                       args=[self.d.slug, self.r.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/docs/%s/revision/%s/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL, self.d.slug,
                self.r.id),
            redirect[0])

        response = post(self.client, 'wiki.delete_revision',
                        args=[self.d.slug, self.r.id])
        redirect = response.redirect_chain[0]
        eq_(302, redirect[1])
        eq_('http://testserver/%s%s?next=/en-US/docs/%s/revision/%s/delete' %
            (settings.LANGUAGE_CODE, settings.LOGIN_URL, self.d.slug,
                self.r.id),
            redirect[0])

    def test_delete_revision_with_permissions(self):
        """Deleting a revision with permissions should work."""
        self.client.login(username='admin', password='testpass')
        response = get(self.client, 'wiki.delete_revision',
                       args=[self.d.slug, self.r.id])
        eq_(200, response.status_code)

        response = post(self.client, 'wiki.delete_revision',
                        args=[self.d.slug, self.r.id])
        eq_(0, Revision.objects.filter(pk=self.r.id).count())

    def test_delete_current_revision(self):
        """Deleting a the current_revision of a document, should update
        the current_revision to previous version."""
        self.client.login(username='admin', password='testpass')
        prev_revision = self.d.current_revision
        prev_revision.save()
        self.r.is_approved = True
        self.r.save()
        d = Document.objects.get(pk=self.d.pk)
        eq_(self.r, d.current_revision)

        post(self.client, 'wiki.delete_revision',
             args=[self.d.slug, self.r.id])
        d = Document.objects.get(pk=d.pk)
        eq_(prev_revision, d.current_revision)


# TODO: Merge with wiki.tests.doc_rev()?
def _create_document(title='Test Document', parent=None,
                     locale=settings.WIKI_DEFAULT_LANGUAGE):
    d = document(title=title, html='<div>Lorem Ipsum</div>',
                 category=10, locale=locale, parent=parent,
                 is_localizable=True)
    d.save()
    r = Revision(document=d, keywords='key1, key2', summary='lipsum',
                 content='<div>Lorem Ipsum</div>', creator_id=8,
                 is_approved=True,
                 comment="Good job!")
    r.save()
    return d


def _translation_data():
    return {
        'title': 'Un Test Articulo', 'slug': 'un-test-articulo',
        'tags': 'tagUno,tagDos,tagTres',
        'keywords': 'keyUno, keyDos, keyTres',
        'summary': 'lipsumo',
        'content': 'loremo ipsumo doloro sito ameto',
        'toc_depth': Revision.TOC_DEPTH_H4}
