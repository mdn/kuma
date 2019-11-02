import time
import urllib

import mock
import pytest
from constance import config
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.sites.models import Site
from django.core import mail
from django.shortcuts import render
from django.test.utils import override_settings
from django.utils import translation
from django.utils.http import urlquote
from django.utils.six.moves.urllib.parse import parse_qs, urlparse
from pyquery import PyQuery as pq

from kuma.core.tests import (assert_no_cache_header,
                             assert_shared_cache_header,
                             call_on_commit_immediately)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams
from kuma.users.models import User
from kuma.users.tests import UserTestCase

from . import (create_topical_parents_docs, document,
               new_document_data, revision, WikiTestCase)
from ..constants import (EXPERIMENT_TITLE_PREFIX, REDIRECT_CONTENT)
from ..events import EditDocumentEvent
from ..models import Document, Revision


DOCUMENT_EDITED_EMAIL_CONTENT = """


admin created a new revision to the document
%s.

To view this document's history, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/docs/%s$history
"""


def test_deletion_log_assert(db, rf):
    """deletion_log.html doesn't render for non-moderators."""
    user = AnonymousUser()
    request = rf.get('/en-US/docs/DeletedDoc')
    request.user = user
    with pytest.raises(RuntimeError) as exc:
        render(request, 'wiki/deletion_log.html')
    assert str(exc.value) == ('Failed assertion: Deletion log details are only'
                              ' for moderators.')


class DocumentTests(UserTestCase, WikiTestCase):
    """Tests for the wiki Document template"""

    def test_document_view(self):
        """Load the document view page and verify the title and content."""
        r = revision(save=True, content='Some text.', is_approved=True)
        response = self.client.get(r.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert (doc('main#content div.document-head h1').text() ==
                str(r.document.title))
        assert doc('article#wikiArticle').text() == r.document.html

    @pytest.mark.breadcrumbs
    def test_document_no_breadcrumbs(self):
        """Create docs with topical parent/child rel, verify no breadcrumbs."""
        d1, d2 = create_topical_parents_docs()
        response = self.client.get(d1.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == d1.title
        assert len(doc('nav.crumbs')) == 0

        response = self.client.get(d2.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == d2.title
        assert len(doc('nav.crumbs')) == 0

    @pytest.mark.breadcrumbs
    def test_document_has_breadcrumbs(self):
        """Documents with parents and a left column have breadcrumbs."""
        d1, d2 = create_topical_parents_docs()
        d1.quick_links_html = '<ul><li>Quick Link</li></ul>'
        d1.save()
        d2.quick_links_html = '<ul><li>Quick Link</li></ul>'
        d2.save()

        response = self.client.get(d1.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == d1.title
        assert len(doc('nav.crumbs')) == 0  # No parents, no breadcrumbs

        response = self.client.get(d2.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == d2.title
        crumbs = "%s\n%s" % (d1.title, d2.title)
        assert doc('nav.crumbs').text() == crumbs

    def test_english_document_no_approved_content(self):
        """Load an English document with no approved content."""
        r = revision(save=True, content='Some text.', is_approved=False)
        response = self.client.get(r.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == str(r.document.title)
        assert ("This article doesn't have approved content yet." ==
                doc('article#wikiArticle').text())

    def test_translation_document_no_approved_content(self):
        """Load a non-English document with no approved content, with a parent
        with no approved content either."""
        r = revision(save=True, content='Some text.', is_approved=False)
        d2 = document(parent=r.document, locale='fr', slug='french', save=True)
        revision(document=d2, save=True, content='Moartext', is_approved=False)
        response = self.client.get(d2.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == str(d2.title)
        # HACK: fr doc has different message if locale/ is updated
        assert (("This article doesn't have approved content yet." in
                 doc('article#wikiArticle').text()) or
                ("Cet article n'a pas encore de contenu" in
                 doc('article#wikiArticle').text()))

    def test_document_fallback_with_translation(self):
        """The document template falls back to English if translation exists
        but it has no approved revisions."""
        r = revision(save=True, content='Test', is_approved=True)
        d2 = document(parent=r.document, locale='fr', slug='french', save=True)
        revision(document=d2, is_approved=False, save=True)
        url = reverse('wiki.document', args=[d2.slug], locale='fr')
        response = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        doc = pq(response.content)
        assert doc('main#content div.document-head h1').text() == str(d2.title)

        # Fallback message is shown.
        assert len(doc('#doc-pending-fallback')) == 1
        assert '$translate' in doc('#edit-button').attr('href')
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        assert pq(r.document.html).text() == doc('article#wikiArticle').text()

    def test_document_fallback_no_translation(self):
        """The document template falls back to English if no translation
        exists."""
        r = revision(save=True, content='Some text.', is_approved=True)
        url = reverse('wiki.document', args=[r.document.slug], locale='fr')
        response = self.client.get(url, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_shared_cache_header(response)
        doc = pq(response.content)
        assert (doc('main#content div.document-head h1').text() ==
                str(r.document.title))

        # Fallback message is shown.
        assert len(doc('#doc-pending-fallback')) == 1
        assert '$translate' in doc('#edit-button').attr('href')
        # Removing this as it shows up in text(), and we don't want to depend
        # on its localization.
        doc('#doc-pending-fallback').remove()
        # Included content is English.
        assert pq(r.document.html).text() == doc('article#wikiArticle').text()

    def test_redirect(self):
        """Make sure documents with REDIRECT directives redirect properly.

        Also check the backlink to the redirect page.
        """
        target = document(save=True)
        target_url = target.get_absolute_url()

        # Ordinarily, a document with no approved revisions cannot have HTML,
        # but we shove it in manually here as a shortcut:
        redirect_html = REDIRECT_CONTENT % dict(title='Boo', href=target_url)
        redirect = document(html=redirect_html)
        redirect.save()
        redirect_url = redirect.get_absolute_url()

        self.client.login(username='admin', password='testpass')
        response = self.client.get(redirect_url, follow=True,
                                   HTTP_HOST=settings.WIKI_HOST)
        self.assertRedirects(response, urlparams(target_url), status_code=301)
        self.assertContains(response, redirect_url)

    def test_redirect_from_nonexistent(self):
        """The template shouldn't crash or print a backlink if the "from" page
        doesn't exist."""
        d = document(save=True)
        response = self.client.get(urlparams(d.get_absolute_url()),
                                   HTTP_HOST=settings.WIKI_HOST)
        self.assertNotContains(response, 'Redirected from ')

    def test_non_localizable_translate_disabled(self):
        """Non localizable document doesn't show tab for 'Localize'."""
        self.client.login(username='testuser', password='testpass')
        d = document(is_localizable=True, save=True)
        resp = self.client.get(d.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
        doc = pq(resp.content)
        assert ('Add a translation' in
                doc('.page-buttons #translations li').text())

        # Make it non-localizable
        d.is_localizable = False
        d.save()
        resp = self.client.get(d.get_absolute_url(),
                               HTTP_HOST=settings.WIKI_HOST)
        doc = pq(resp.content)
        assert ('Add a translation' not in
                doc('.page-buttons #translations li').text())

    @pytest.mark.toc
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
        response = self.client.get(r.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        assert b'<div id="toc"' in response.content
        new_r = revision(document=r.document, content=r.content,
                         toc_depth=0, is_approved=True)
        new_r.save()
        response = self.client.get(r.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        assert b'<div class="page-toc">' not in response.content

    def test_lang_switcher_footer(self):
        """Test the language switcher footer"""
        parent = document(locale=settings.WIKI_DEFAULT_LANGUAGE, save=True)
        trans_bn = document(parent=parent, locale="bn", save=True)
        trans_ar = document(parent=parent, locale="ar", save=True)
        trans_pt_br = document(parent=parent, locale="pt-BR", save=True)
        trans_fr = document(parent=parent, locale="fr", save=True)

        response = self.client.get(trans_pt_br.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        options = doc(".languages.go select.wiki-l10n option")

        # The requeseted document language name should be at first
        assert trans_pt_br.language in options[0].text
        assert parent.language not in options[0].text
        # The parent document language should be at at second
        assert parent.language in options[1].text
        assert trans_ar.language not in options[1].text
        # Then should be ar, bn, fr
        assert trans_ar.language in options[2].text
        assert trans_bn.language in options[3].text
        assert trans_fr.language in options[4].text

    def test_lang_switcher_button(self):
        parent = document(locale=settings.WIKI_DEFAULT_LANGUAGE, save=True)
        trans_bn = document(parent=parent, locale="bn", save=True)
        trans_ar = document(parent=parent, locale="ar", save=True)
        trans_pt_br = document(parent=parent, locale="pt-BR", save=True)
        trans_fr = document(parent=parent, locale="fr", save=True)

        response = self.client.get(trans_pt_br.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        options = doc("#languages-menu-submenu ul#translations li a")

        # The requeseted document language name should not be at button
        assert trans_pt_br.language not in options[0].text
        # Parent document language name should be at first
        assert parent.language in options[0].text
        # Then should be ar, bn, fr
        assert trans_ar.language in options[1].text
        assert trans_bn.language in options[2].text
        assert trans_fr.language in options[3].text

    def test_experiment_document_view(self):
        slug = EXPERIMENT_TITLE_PREFIX + 'Test'
        r = revision(save=True, content='Experiment.', is_approved=True,
                     slug=slug)
        assert r.document.is_experiment
        response = self.client.get(r.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        doc = pq(response.content)
        doc_title = doc('main#content div.document-head h1').text()
        assert doc_title == str(r.document.title)
        assert doc('article#wikiArticle').text() == r.document.html
        metas = doc("meta[name='robots']")
        assert len(metas) == 1
        meta_content = metas[0].get('content')
        assert meta_content == 'noindex, nofollow'
        doc_experiment = doc('div#doc-experiment')
        assert len(doc_experiment) == 1


_TEST_CONTENT_EXPERIMENTS = [{
    'id': 'experiment-test',
    'ga_name': 'experiment-test',
    'param': 'v',
    'pages': {
        'en-US:Original': {
            'control': 'Original',
            'test': 'Experiment:Test/Variant',
        }
    }
}]
_PIPELINE = settings.PIPELINE
_PIPELINE['JAVASCRIPT']['experiment-test'] = {
    'output_filename': 'build/js/experiment-framework-test.js',
}


@override_settings(CONTENT_EXPERIMENTS=_TEST_CONTENT_EXPERIMENTS,
                   PIPELINE=_PIPELINE,
                   GOOGLE_ANALYTICS_ACCOUNT='fake')
class DocumentContentExperimentTests(UserTestCase, WikiTestCase):

    # src attribute of the content experiment <script> tag
    # Can't use pyquery for <head> elements
    script_src = ('src="%sbuild/js/experiment-framework-test.js"' %
                  settings.STATIC_URL)

    # Googla Analytics custom dimension calls
    expected_15 = "ga('set', 'dimension15', 'experiment-test:test')"
    expected_16 = "ga('set', 'dimension16', '/en-US/docs/Original')"

    def test_anon_no_variant_selected(self):
        """Anonymous users get the experiment script on the original page."""
        rev = revision(save=True, content='Original Content.', is_approved=True,
                       slug='Original')
        response = self.client.get(rev.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert b'Original Content.' in response.content
        assert b'dimension15' not in response.content
        assert self.script_src.encode('utf-8') in response.content

    def test_user_no_variant_selected(self):
        """Users get original page without the experiment script."""
        rev = revision(save=True, content='Original Content.', is_approved=True,
                       slug='Original')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(rev.document.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert self.script_src.encode('utf-8') not in response.content

    def test_anon_valid_variant_selected(self):
        """Anon users are in the Google Analytics cohort on the variant."""
        rev = revision(save=True, content='Original Content.', is_approved=True,
                       slug='Original')
        revision(save=True, content='Variant Content.', is_approved=True,
                 slug='Experiment:Test/Variant')
        response = self.client.get(rev.document.get_absolute_url(),
                                   {'v': 'test'}, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert b'Original Content.' not in response.content
        assert b'Variant Content.' in response.content
        assert self.expected_15.encode('utf-8') in response.content
        assert self.expected_16.encode('utf-8') in response.content
        assert self.script_src.encode('utf-8') not in response.content
        doc = pq(response.content)
        assert not doc('#edit-button')

    def test_user_valid_variant_selected(self):
        """Users are not added to the Google Analytics cohort on the variant."""
        rev = revision(save=True, content='Original Content.', is_approved=True,
                       slug='Original')
        revision(save=True, content='Variant Content.', is_approved=True,
                 slug='Experiment:Test/Variant')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(rev.document.get_absolute_url(),
                                   {'v': 'test'}, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert 'Original Content.' not in content
        assert 'Variant Content.' in content
        assert self.expected_15 not in content
        assert self.expected_16 not in content
        assert self.script_src not in content
        doc = pq(response.content)
        assert not doc('#edit-button')


@override_settings(GOOGLE_ANALYTICS_ACCOUNT='fake')
class GoogleAnalyticsTests(UserTestCase, WikiTestCase):

    ga_create = "ga('create', 'fake', 'mozilla.org');"
    dim1 = "ga('set', 'dimension1', 'Yes');"
    dim2 = "ga('set', 'dimension2', 'Yes');"
    dim17_tmpl = "ga('set', 'dimension17', '%s');"
    dim18 = "ga('set', 'dimension18', 'Yes');"

    def test_en_doc(self):
        doc = _create_document()
        assert doc.slug
        response = self.client.get(doc.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        dim17 = self.dim17_tmpl % doc.slug
        assert dim17 in content

    def test_fr_doc(self):
        en_doc = _create_document(title='English Document')
        fr_doc = _create_document(title='Document Français',
                                  parent=en_doc, locale='fr')
        assert en_doc.slug != fr_doc.slug
        response = self.client.get(fr_doc.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        dim17 = self.dim17_tmpl % en_doc.slug
        assert dim17 in content

    def test_orphan_doc(self):
        orphan_doc = _create_document(title='Huérfano', locale='es')
        response = self.client.get(orphan_doc.get_absolute_url(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        dim17 = "ga('set', 'dimension17',"
        assert dim17 not in content

    def test_anon_user(self):
        response = self.client.get('/en-US/', HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        assert self.dim1 not in content
        assert self.dim2 not in content
        assert self.dim18 not in content

    def test_regular_user(self):
        assert self.client.login(username='testuser', password='testpass')
        response = self.client.get('/en-US/', HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        assert self.dim1 in content
        assert self.dim2 not in content
        assert self.dim18 not in content

    def test_beta_user(self):
        testuser = User.objects.get(username='testuser')
        beta = Group.objects.get(name='Beta Testers')
        testuser.groups.add(beta)
        assert self.client.login(username='testuser', password='testpass')
        response = self.client.get('/en-US/', HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        assert self.dim1 in content
        assert self.dim2 in content
        assert self.dim18 not in content

    def test_staff_user(self):
        assert self.client.login(username='admin', password='testpass')
        response = self.client.get('/en-US/', HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        content = response.content.decode(response.charset)
        assert self.ga_create in content
        assert self.dim1 in content
        assert self.dim2 not in content
        assert self.dim18 in content


def test_revision_template(root_doc, client):
    """Verify the revision template."""
    rev = root_doc.current_revision
    url = reverse('wiki.revision', args=[root_doc.slug, rev.id])
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_shared_cache_header(response)
    page = pq(response.content)
    assert page('h1').text() == 'Revision %s of %s' % (rev.id, root_doc.title)
    assert page('#doc-source pre').text() == rev.content
    assert page('span[data-name="slug"]').text() == root_doc.slug
    assert page('span[data-name="title"]').text() == root_doc.title
    assert page('span[data-name="id"]').text() == str(rev.id)
    expected_date = 'Apr 14, 2017, 12:15:00 PM'
    assert page('span[data-name="created"]').text() == expected_date
    assert page('span[data-name="creator"]').text() == rev.creator.username
    assert page('span[data-name="comment"]').text() == rev.comment
    is_current = page('span[data-name="is-current"]')
    assert is_current.text() == "Yes"
    assert is_current.attr['data-value'] == "1"


class NewDocumentTests(UserTestCase, WikiTestCase):
    """Tests for the New Document template"""

    def test_new_document_GET_with_perm(self):
        """HTTP GET to new document URL renders the form."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.create'),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert 1 == len(doc('form#wiki-page-edit input[name="title"]'))

    def test_new_document_includes_review_block(self):
        """
        New document page includes 'Review Needed?' section.
        https://bugzil.la/1052047
        """
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.create'),
                                   HTTP_HOST=settings.WIKI_HOST)

        test_strings = ['Review needed?', 'Technical', 'Editorial']
        assert 200 == response.status_code

        # TODO: push test_strings functionality up into a test helper
        content = response.content.decode(response.charset)
        for test_string in test_strings:
            assert test_string in content

    def test_new_document_preview_button(self):
        """HTTP GET to new document URL shows preview button."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.create'),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        assert len(doc('.btn-preview'))

    def test_new_document_form_defaults(self):
        """The new document form should have all all 'Relevant to' options
        checked by default."""
        self.client.login(username='admin', password='testpass')
        response = self.client.get(reverse('wiki.create'),
                                   HTTP_HOST=settings.WIKI_HOST)
        doc = pq(response.content)
        assert "Name Your Article" == doc('input#id_title').attr('placeholder')

    @mock.patch.object(Site.objects, 'get_current')
    def test_new_document_POST(self, get_current):
        """HTTP POST to new document URL creates the document."""
        get_current.return_value.domain = 'testserver'

        self.client.login(username='admin', password='testpass')
        tags = ['tag1', 'tag2']
        data = new_document_data(tags)
        response = self.client.post(reverse('wiki.create'), data,
                                    follow=True, HTTP_HOST=settings.WIKI_HOST)
        d = Document.objects.get(title=data['title'])
        assert len(response.redirect_chain) == 1
        redirect_uri, status_code = response.redirect_chain[0]
        assert redirect_uri == ('/en-US/docs/%s' % d.slug)
        assert status_code == 302
        assert settings.WIKI_DEFAULT_LANGUAGE == d.locale
        assert tags == sorted(t.name for t in d.tags.all())
        r = d.revisions.all()[0]
        assert data['keywords'] == r.keywords
        assert data['summary'] == r.summary
        assert data['content'] == r.content

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
        self.client.post(reverse('wiki.create', locale=locale),
                         data, follow=True, HTTP_HOST=settings.WIKI_HOST)
        d = Document.objects.get(title=data['title'])
        assert locale == d.locale

    def test_new_document_POST_empty_title(self):
        """Trigger required field validation for title."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data(['tag1', 'tag2'])
        data['title'] = ''
        response = self.client.post(reverse('wiki.create'), data,
                                    follow=True, HTTP_HOST=settings.WIKI_HOST)
        doc = pq(response.content)
        ul = doc('article ul.errorlist')
        assert len(ul)
        assert 'Please provide a title.' in ul('li').text()

    def test_new_document_POST_empty_content(self):
        """Trigger required field validation for content."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data(['tag1', 'tag2'])
        data['content'] = ''
        response = self.client.post(reverse('wiki.create'), data,
                                    follow=True, HTTP_HOST=settings.WIKI_HOST)
        doc = pq(response.content)
        ul = doc('article ul.errorlist')
        assert 1 == len(ul)
        assert 'Please provide content.' == ul('li').text()

    def test_slug_collision_validation(self):
        """Trying to create document with existing locale/slug should
        show validation error."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = d.slug
        response = self.client.post(reverse('wiki.create'), data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert 200 == response.status_code
        doc = pq(response.content)
        ul = doc('article ul.errorlist')
        assert 1 == len(ul)
        assert ('Document with this Slug and Locale already exists.' ==
                ul('li').text())

    def test_title_no_collision(self):
        """Only slugs and not titles are required to be unique per
        locale now, so test that we actually allow that."""
        d = _create_document()
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = '%s-once-more-with-feeling' % d.slug
        response = self.client.post(reverse('wiki.create'), data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert 302 == response.status_code

    def test_slug_3_chars(self):
        """Make sure we can create a slug with only 3 characters."""
        self.client.login(username='admin', password='testpass')
        data = new_document_data()
        data['slug'] = 'ask'
        response = self.client.post(reverse('wiki.create'), data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert 302 == response.status_code
        assert 'ask' == Document.objects.all()[0].slug


class NewRevisionTests(UserTestCase, WikiTestCase):
    """Tests for the New Revision template"""

    def setUp(self):
        super(NewRevisionTests, self).setUp()
        self.d = _create_document()
        self.username = 'admin'
        self.client.login(username=self.username, password='testpass')

    def test_new_revision_GET_logged_out(self):
        """Creating a revision without being logged in redirects to login page.
        """
        self.client.logout()
        response = self.client.get(reverse('wiki.edit', args=[self.d.slug]),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302

    def test_new_revision_GET_with_perm(self):
        """HTTP GET to new revision URL renders the form."""
        response = self.client.get(reverse('wiki.edit', args=[self.d.slug]),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        doc = pq(response.content)
        assert len(doc('article#edit-document '
                       'form#wiki-page-edit textarea[name="content"]')) == 1

    @override_settings(TIDINGS_CONFIRM_ANONYMOUS_WATCHES=False)
    @call_on_commit_immediately
    def test_new_revision_POST_document_with_current(self):
        """HTTP POST to new revision URL creates the revision on a document.

        The document in this case already has a current_revision, therefore
        the document document fields are not editable.

        Also assert that the edited and reviewable notifications go out.
        """
        # Sign up for notifications:
        EditDocumentEvent.notify('sam@example.com', self.d).activate().save()

        # Edit a document
        data = {
            'summary': 'A brief summary',
            'content': 'The article content',
            'keywords': 'keyword1 keyword2',
            'slug': self.d.slug,
            'toc_depth': 1,
            'based_on': self.d.current_revision.id,
            'form-type': 'rev',
        }
        edit_url = reverse('wiki.edit', args=[self.d.slug])
        response = self.client.post(edit_url, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert self.d.revisions.count() == 2
        new_rev = self.d.revisions.order_by('-id')[0]
        assert self.d.current_revision == new_rev.based_on

        # Assert notifications fired and have the expected content:
        # 1 email for the first time edit notification
        # 1 email for the EditDocumentEvent to sam@example.com
        # Regression check:
        # messing with context processors can
        # cause notification emails to error
        # and stop being sent.
        time.sleep(1)
        assert 2 == len(mail.outbox)
        first_edit_email = mail.outbox[0]
        expected_to = [config.EMAIL_LIST_SPAM_WATCH]
        expected_subject = (
            '[MDN][%(loc)s] %(user)s made their first edit, to: %(title)s' %
            {'loc': self.d.locale,
             'user': new_rev.creator.username,
             'title': self.d.title}
        )
        assert expected_subject == first_edit_email.subject
        assert expected_to == first_edit_email.to

        edited_email = mail.outbox[1]
        expected_to = ['sam@example.com']
        expected_subject = ('[MDN][en-US] Page "%s" changed by %s'
                            % (self.d.title, new_rev.creator))

        assert expected_subject == edited_email.subject
        assert expected_to == edited_email.to

        assert ('{} changed {}.'.format(self.username, self.d.title) in
                edited_email.body)

        assert (self.d.get_full_url() + '$history') in edited_email.body
        assert 'utm_campaign=' in edited_email.body

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
        data['form-type'] = 'rev'
        response = self.client.post(reverse('wiki.edit', args=[self.d.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert self.d.revisions.count() == 2

        new_rev = self.d.revisions.order_by('-id')[0]
        # There are no approved revisions, so it's based_on nothing:
        assert new_rev.based_on is None
        assert edited_fire.called

    def test_new_revision_POST_removes_old_tags(self):
        """Changing the tags on a document removes the old tags from
        that document."""
        self.d.current_revision = None
        self.d.save()
        tags = ['tag1', 'tag2', 'tag3']
        self.d.tags.add(*tags)
        result_tags = sorted(self.d.tags.names())
        assert tags == result_tags
        tags = ['tag1', 'tag4']
        data = new_document_data(tags)
        data['form-type'] = 'rev'
        response = self.client.post(reverse('wiki.edit', args=[self.d.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        result_tags = list(self.d.tags.names())
        result_tags.sort()
        assert tags == result_tags

    def test_new_form_maintains_based_on_rev(self):
        """Revision.based_on should be the rev that was current when the Edit
        button was clicked, even if other revisions happen while the user is
        editing."""
        _test_form_maintains_based_on_rev(
            self.client, self.d, 'wiki.edit',
            {'summary': 'Windy', 'content': 'gerbils', 'form-type': 'rev',
             'slug': self.d.slug, 'toc_depth': 1},
            locale='en-US')


class DocumentEditTests(UserTestCase, WikiTestCase):
    """Test the editing of document level fields."""

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
        response = self.client.get(reverse('wiki.edit', args=[self.d.slug]),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)

        data = new_document_data()
        new_title = 'A brand new title'
        data.update(title=new_title)
        data['form-type'] = 'doc'
        data.update(is_localizable='True')
        response = self.client.post(reverse('wiki.edit', args=[self.d.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert Document.objects.get(pk=self.d.pk).title == new_title

    def test_change_slug_case(self):
        """Changing the case of some letters in the slug should work."""
        data = new_document_data()
        new_slug = 'Test-Document'
        data.update(slug=new_slug)
        data['form-type'] = 'doc'
        response = self.client.post(reverse('wiki.edit', args=[self.d.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert Document.objects.get(pk=self.d.pk).slug == new_slug

    def test_change_title_case(self):
        """Changing the case of some letters in the title should work."""
        data = new_document_data()
        new_title = 'TeST DoCuMent'
        data.update(title=new_title)
        data['form-type'] = 'doc'
        response = self.client.post(reverse('wiki.edit', args=[self.d.slug]),
                                    data, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert Document.objects.get(pk=self.d.pk).title == new_title


def test_compare_revisions(edit_revision, client):
    """Comparing two valid revisions of the same document works."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()
    params = {'from': first_revision.id, 'to': edit_revision.id}
    url = urlparams(reverse('wiki.compare_revisions', args=[doc.slug]),
                    **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_shared_cache_header(response)
    page = pq(response.content)
    assert page('span.diff_sub').text() == 'Getting\xa0started...'
    assert page('span.diff_add').text() == 'The\xa0root\xa0document.'

    change_link = page('a.change-revisions')
    assert change_link.text() == 'Change Revisions'
    change_href = change_link.attr('href')
    bits = urlparse(change_href)
    assert bits.path == reverse('wiki.document_revisions', args=[doc.slug])
    assert parse_qs(bits.query) == {'locale': [doc.locale],
                                    'origin': ['compare']}

    rev_from_link = page('div.rev-from h3 a')
    assert rev_from_link.text() == 'Revision %d:' % first_revision.id
    from_href = rev_from_link.attr('href')
    assert from_href == reverse('wiki.revision',
                                args=[doc.slug, first_revision.id])

    rev_to_link = page('div.rev-to h3 a')
    assert rev_to_link.text() == 'Revision %d:' % edit_revision.id
    to_href = rev_to_link.attr('href')
    assert to_href == reverse('wiki.revision',
                              args=[doc.slug, edit_revision.id])


def test_compare_first_translation(trans_revision, client):
    """A localized revision can be compared to an English source revision."""
    fr_doc = trans_revision.document
    en_revision = trans_revision.based_on
    en_doc = en_revision.document
    assert en_doc != fr_doc
    params = {'from': en_revision.id, 'to': trans_revision.id}
    url = urlparams(reverse('wiki.compare_revisions', args=[fr_doc.slug],
                            locale=fr_doc.locale), **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response['X-Robots-Tag'] == 'noindex'
    assert_shared_cache_header(response)
    page = pq(response.content)
    assert page('span.diff_sub').text() == 'Getting\xa0started...'
    assert page('span.diff_add').text() == 'Mise\xa0en\xa0route...'

    # Change Revisions link goes to the French document history page
    change_link = page('a.change-revisions')
    change_href = change_link.attr('href')
    bits = urlparse(change_href)
    assert bits.path == reverse('wiki.document_revisions', args=[fr_doc.slug],
                                locale=fr_doc.locale)
    assert parse_qs(bits.query) == {'locale': [fr_doc.locale],
                                    'origin': ['compare']}

    # From revision link goes to the English document
    rev_from_link = page('div.rev-from h3 a')
    from_href = rev_from_link.attr('href')
    assert from_href == reverse('wiki.revision',
                                args=[en_doc.slug, en_revision.id],
                                locale=en_doc.locale)

    # To revision link goes to the French document
    rev_to_link = page('div.rev-to h3 a')
    to_href = rev_to_link.attr('href')
    assert to_href == reverse('wiki.revision',
                              args=[fr_doc.slug, trans_revision.id],
                              locale=fr_doc.locale)


class TranslateTests(UserTestCase, WikiTestCase):
    """Tests for the Translate page"""

    def setUp(self):
        super(TranslateTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def _translate_uri(self):
        translate_uri = reverse('wiki.translate', args=[self.d.slug])
        return '%s?tolocale=%s' % (translate_uri, 'es')

    def test_translate_GET_logged_out(self):
        """Try to create a translation while logged out."""
        self.client.logout()
        translate_uri = self._translate_uri()
        response = self.client.get(translate_uri, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert_no_cache_header(response)
        expected_url = '%s?next=%s' % (reverse('account_login'),
                                       urlquote(translate_uri))
        assert expected_url in response['Location']

    def test_translate_GET_with_perm(self):
        """HTTP GET to translate URL renders the form."""
        response = self.client.get(self._translate_uri(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        doc = pq(response.content)
        assert len(doc('form textarea[name="content"]')) == 1
        # initial translation should include slug input
        assert len(doc('form input[name="slug"]')) == 1
        assert ('Espa' in doc('div.title-locale').text())

    def test_translate_disallow(self):
        """HTTP GET to translate URL returns 400 when not localizable."""
        self.d.is_localizable = False
        self.d.save()
        response = self.client.get(self._translate_uri(),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 400
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)

    def test_invalid_document_form(self):
        """Make sure we handle invalid document form without a 500."""
        translate_uri = self._translate_uri()
        data = _translation_data()
        data['slug'] = ''  # Invalid slug
        response = self.client.post(translate_uri, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)

    def test_invalid_revision_form(self):
        """When creating a new translation, an invalid revision form shouldn't
        result in a new Document being created."""
        translate_uri = self._translate_uri()
        data = _translation_data()
        data['content'] = ''  # Content is required
        response = self.client.post(translate_uri, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert self.d.translations.count() == 0

    @mock.patch.object(EditDocumentEvent, 'fire')
    @mock.patch.object(Site.objects, 'get_current')
    def test_first_translation_to_locale(self, get_current, edited_fire):
        """Create the first translation of a doc to new locale."""
        get_current.return_value.domain = 'testserver'

        translate_uri = self._translate_uri()
        data = _translation_data()
        response = self.client.post(translate_uri, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        new_doc = Document.objects.get(slug=data['slug'])
        assert new_doc.locale == 'es'
        assert new_doc.title == data['title']
        assert new_doc.parent == self.d
        rev = new_doc.revisions.all()[0]
        assert rev.keywords == data['keywords']
        assert rev.summary == data['summary']
        assert rev.content == data['content']
        assert edited_fire.called

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
        response = self.client.get(translate_uri, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        doc = pq(response.content)
        assert doc('#id_content').text() == rev_es.content
        assert (doc('article.approved .translate-rendered').text() ==
                rev_enUS.content)

        # Post the translation and verify
        data = _translation_data()
        data['content'] = 'loremo ipsumo doloro sito ameto nuevo'
        response = self.client.post(translate_uri, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert response['Location'] == '/es/docs/un-test-articulo?rev_saved='
        doc = Document.objects.get(slug=data['slug'])
        rev = doc.revisions.filter(content=data['content'])[0]
        assert rev.keywords == data['keywords']
        assert rev.summary == data['summary']
        assert rev.content == data['content']
        assert edited_fire.called

        # subsequent translations should NOT include slug input
        self.client.logout()
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(translate_uri, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        doc = pq(response.content)
        assert len(doc('form input[name="slug"]')) == 0

    def test_translate_form_maintains_based_on_rev(self):
        """
        Revision.based_on should be the rev that was current when the
        Translate button was clicked, even if other revisions happen while the
        user is editing.
        """
        _test_form_maintains_based_on_rev(self.client,
                                          self.d,
                                          'wiki.translate',
                                          _translation_data(),
                                          trans_lang='es',
                                          locale='en-US')

    def test_translate_update_doc_only(self):
        """
        Submitting the document form should update document.
        No new revisions should be created.
        """
        rev_es = self._create_and_approve_first_translation()
        translate_uri = self._translate_uri()
        data = _translation_data()
        new_title = 'Un nuevo titulo'
        data['title'] = new_title
        data['form-type'] = 'doc'
        response = self.client.post(translate_uri, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert response['location'].endswith(
            '/es/docs/un-test-articulo$edit?opendescription=1')
        revisions = rev_es.document.revisions.all()
        assert revisions.count() == 1  # No new revisions
        d = Document.objects.get(id=rev_es.document.id)
        assert d.title == new_title  # Title is updated

    def test_translate_update_rev_and_doc(self):
        """
        Submitting the revision form should create a new revision.
        And since Kuma docs default to approved, should update doc too.
        """
        rev_es = self._create_and_approve_first_translation()
        translate_uri = self._translate_uri()
        data = _translation_data()
        new_title = 'Un nuevo titulo'
        data['title'] = new_title
        data['form'] = 'rev'
        response = self.client.post(translate_uri, data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        assert response['location'].endswith(
            '/es/docs/un-test-articulo?rev_saved=')
        revisions = rev_es.document.revisions.all()
        assert revisions.count() == 2  # New revision is created
        d = Document.objects.get(id=rev_es.document.id)
        assert d.title == data['title']  # Title isn't updated

    def test_translate_form_content_fallback(self):
        """
        If there are existing but unapproved translations, prefill
        content with latest.
        """
        self.test_first_translation_to_locale()
        translate_uri = self._translate_uri()
        response = self.client.get(translate_uri, HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert response['X-Robots-Tag'] == 'noindex'
        assert_no_cache_header(response)
        doc = pq(response.content)
        document = Document.objects.filter(locale='es')[0]
        existing_rev = document.revisions.all()[0]
        assert doc('#id_content').text() == existing_rev.content


def _test_form_maintains_based_on_rev(client, doc, view, post_data,
                                      trans_lang=None, locale=None):
    """Confirm that the based_on value set in the revision created by an edit
    or translate form is the current_revision of the document as of when the
    form was first loaded, even if other revisions have been approved in the
    meantime."""
    if trans_lang:
        translate_path = doc.slug
        uri = urllib.parse.quote(
            reverse('wiki.translate',
                    locale=trans_lang,
                    args=[translate_path]))
    else:
        uri = reverse(view, locale=locale, args=[doc.slug])
    response = client.get(uri, HTTP_HOST=settings.WIKI_HOST)
    assert response['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(response)
    orig_rev = doc.current_revision
    assert (int(pq(response.content)('input[name=based_on]').attr('value')) ==
            orig_rev.id)

    # While Fred is editing the above, Martha approves a new rev:
    martha_rev = revision(document=doc)
    martha_rev.is_approved = True
    martha_rev.save()

    # Then Fred saves his edit:
    post_data_copy = {'based_on': orig_rev.id, 'slug': orig_rev.slug}
    post_data_copy.update(post_data)  # Don't mutate arg.
    response = client.post(uri, data=post_data_copy,
                           HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code in (200, 302)
    assert response['X-Robots-Tag'] == 'noindex'
    assert_no_cache_header(response)
    fred_rev = Revision.objects.all().order_by('-id')[0]
    assert fred_rev.based_on == orig_rev


class ArticlePreviewTests(UserTestCase, WikiTestCase):
    """Tests for preview view and template."""

    def setUp(self):
        super(ArticlePreviewTests, self).setUp()
        self.client.login(username='testuser', password='testpass')

    def test_preview_GET_405(self):
        """Preview with HTTP GET results in 405."""
        response = self.client.get(reverse('wiki.preview'),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 405
        assert_no_cache_header(response)

    def test_preview(self):
        """Preview the wiki syntax content."""
        response = self.client.post(reverse('wiki.preview'),
                                    {'content': '<h1>Test Content</h1>'},
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_no_cache_header(response)
        doc = pq(response.content)
        assert doc('article#wikiArticle h1').text() == 'Test Content'

    @pytest.mark.xfail(reason='broken test')
    def test_preview_locale(self):
        """Preview the wiki syntax content."""
        # Create a test document and translation.
        d = _create_document()
        _create_document(title='Prueba', parent=d, locale='es')
        # Preview content that links to it and verify link is in locale.
        url = reverse('wiki.preview', locale='es')
        response = self.client.post(url, {'content': '[[Test Document]]'},
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_no_cache_header(response)
        doc = pq(response.content)
        link = doc('#doc-content a')
        assert link.text() == 'Prueba'
        assert '/es/docs/prueba' == link[0].attrib['href']


class SelectLocaleTests(UserTestCase, WikiTestCase):
    """Test the locale selection page"""

    def setUp(self):
        super(SelectLocaleTests, self).setUp()
        self.d = _create_document()
        self.client.login(username='admin', password='testpass')

    def test_page_renders_locales(self):
        """Load the page and verify it contains all the locales for l10n."""
        response = self.client.get(reverse('wiki.select_locale',
                                           args=[self.d.slug]),
                                   HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_no_cache_header(response)
        doc = pq(response.content)
        assert (len(doc('#select-locale ul.locales li')) ==
                len(settings.LANGUAGES) - 1)  # All except for 1 (en-US)


def _create_document(title='Test Document', parent=None,
                     locale=settings.WIKI_DEFAULT_LANGUAGE):
    d = document(title=title, html='<div>Lorem Ipsum</div>',
                 locale=locale, parent=parent, is_localizable=True)
    d.save()
    r = Revision(document=d, keywords='key1, key2', summary='lipsum',
                 content='<div>Lorem Ipsum</div>', creator_id=8,
                 is_approved=True,
                 comment="Good job!")
    r.save()
    return d


def _translation_data():
    return {
        'title': 'Un Test Articulo',
        'slug': 'un-test-articulo',
        'tags': 'tagUno,tagDos,tagTres',
        'keywords': 'keyUno, keyDos, keyTres',
        'summary': 'lipsumo',
        'content': 'loremo ipsumo doloro sito ameto',
        'toc_depth': Revision.TOC_DEPTH_H4,
    }


@pytest.mark.parametrize("elem_num,has_prev,is_english,has_revert", [
    (0, True, False, False),
    (1, True, False, True),
    (2, False, True, False)],
    ids=['current', 'first_trans', 'en_source'])
def test_list_revisions(elem_num, has_prev, is_english, has_revert,
                        admin_client, trans_edit_revision):
    """Check the three rows of the test translation.

    Row 1: The latest edit of the translation
    Row 2: The first translation into French
    Row 3: The English revision that the first translation was based on
    """
    doc = trans_edit_revision.document
    url = reverse('wiki.document_revisions', locale=doc.locale,
                  args=[doc.slug])
    response = admin_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200

    page = pq(response.content)
    list_items = page('ul.revision-list li')

    # Select the list item and revision requested in the test
    li_element = list_items[elem_num]
    revision = trans_edit_revision
    num = 0
    while num < elem_num:
        revision = revision.previous
        num += 1
    rev_doc = revision.document

    # The date text links to the expected revision page
    revision_url = reverse('wiki.revision',
                           locale=rev_doc.locale,
                           args=[rev_doc.slug, revision.id])
    rev_link = li_element.cssselect('.revision-list-date')[0].find('a')
    assert rev_link.attrib['href'] == revision_url

    # Check if there is a previous link
    prev_link = li_element.cssselect('.revision-list-prev')[0].find('a')
    if has_prev:
        assert prev_link is not None
        with translation.override(doc.locale):
            expected = translation.gettext('Previous')
        assert prev_link.text == expected
    else:
        assert prev_link is None

    # The comment has a marker if it is the English source page
    comment_em = li_element.cssselect('.revision-list-comment')[0].find('em')
    if is_english:
        assert li_element.attrib['class'] == 'revision-list-en-source'
        with translation.override(doc.locale):
            expected = translation.gettext('English (US)')
        assert comment_em.text == expected
    else:
        assert li_element.attrib.get('class') is None
        assert comment_em is None

    # The revert button is included if it makes sense for the revision
    revert = li_element.cssselect('.revision-list-revert')
    if has_revert:
        assert len(revert) == 1
    else:
        assert len(revert) == 0
