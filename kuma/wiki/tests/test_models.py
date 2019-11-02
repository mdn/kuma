import time
from datetime import date, datetime, timedelta
from xml.sax.saxutils import escape

import mock
import pytest
from constance import config
from constance.test import override_config
from django.conf import settings
from django.core.exceptions import ValidationError
from six.moves.urllib.parse import urlparse

from kuma.attachments.models import Attachment, AttachmentRevision
from kuma.core.exceptions import ProgrammingError
from kuma.core.tests import get_user
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

from . import create_document_tree, document, revision
from .. import tasks
from ..constants import EXPERIMENT_TITLE_PREFIX, REDIRECT_CONTENT
from ..events import EditDocumentInTreeEvent
from ..exceptions import (DocumentRenderedContentNotAvailable,
                          DocumentRenderingInProgress, PageMoveError)
from ..models import (Document, DocumentTag, Revision, RevisionIP,
                      TaggedDocument)
from ..utils import tidy_content


def test_clean_current_revision_with_no_change(root_doc, wiki_user_2):
    assert root_doc.clean_current_revision(wiki_user_2) is None


def test_clean_current_revision_with_no_current(root_doc, wiki_user_2):
    root_doc.current_revison = None
    assert root_doc.clean_current_revision(wiki_user_2) is None


@pytest.mark.parametrize('is_approved', (True, False))
@pytest.mark.parametrize('doc_case', ('default-language', 'translation'))
def test_clean_current_revision(root_doc, trans_doc, wiki_user_2, doc_case,
                                is_approved):
    doc = trans_doc if doc_case == 'translation' else root_doc
    original_doc_slug = doc.slug
    original_doc_title = doc.title
    current_rev = doc.current_revision
    current_rev.content = (
        '<div onclick="alert(\'hacked!\')">click me</div>'
    )
    current_rev.tidied_content = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
        <html>
          <head>
            <title></title>
          </head>
          <body>
            <div onclick="alert('hacked!')">
              click me
            </div>
          </body>
        </html>
    """
    tags = '"Banana" "Orange" "Apple"'
    l10n_tags = {'inprogress'}
    review_tags = {'editorial', 'technical'}
    current_rev.tags = tags
    # Let's make the revision's slug and title different from the document
    # to ensure that they're corrected in the end.
    current_rev.slug = original_doc_slug + 's'
    current_rev.title = original_doc_title + 's'
    current_rev.is_approved = is_approved
    current_rev.localization_tags.set(*l10n_tags)
    current_rev.review_tags.set(*review_tags)
    prior_pk = current_rev.pk
    prior_creator = current_rev.creator
    prior_created = current_rev.created
    if doc_case == 'translation':
        expected_based_on_pk = current_rev.based_on.pk
    else:
        expected_based_on_pk = current_rev.pk
    rev = doc.clean_current_revision(wiki_user_2)
    assert rev
    assert rev.pk != prior_pk
    assert rev.creator != prior_creator
    assert rev.creator == wiki_user_2
    assert rev.created > prior_created
    assert rev.based_on.pk == expected_based_on_pk
    assert rev.content == '<div>click me</div>'
    assert rev.tidied_content == (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">\n'
        '<html>\n'
        '  <head>\n'
        '    <title></title>\n'
        '  </head>\n'
        '  <body>\n'
        '    <div>\n'
        '      click me\n'
        '    </div>\n'
        '  </body>\n'
        '</html>\n'
    )
    assert rev.tags == tags
    assert set(t.name for t in rev.localization_tags.all()) == l10n_tags
    assert set(t.name for t in rev.review_tags.all()) == review_tags
    assert rev.comment == 'Clean prior revision of {} by {}'.format(
        prior_created, prior_creator)
    assert rev.slug == original_doc_slug
    assert rev.title == original_doc_title
    assert doc.current_revision.pk == rev.pk


def test_document_is_not_experiment():
    """A document without the experiment prefix is not an experiment."""
    doc = Document(slug='test')
    assert not doc.is_experiment


def test_document_is_experiment():
    """A document with the experiment prefix is an experiment."""
    doc = Document(slug=EXPERIMENT_TITLE_PREFIX + 'test')
    assert doc.is_experiment


@pytest.mark.parametrize('slug,legacy', [
    # See LEGACY_MINDTOUCH_NAMESPACES in ../constants.py
    ('Help:Login', True),
    ('Help_talk:Login', True),
    ('Project:MDN', True),
    ('Project_talk:MDN', True),
    ('Special:easter_egg', True),
    ('Talk:Web:CSS', True),
    ('Template:domxref', True),
    ('Template_talk:domxref', True),
    ('User:jezdez', True),
    ('User_talk:jezdez', True),
    # Experiments aren't legacy yet
    ('Experiment:Blue', False),
    # Slugs without colons don't have namespaces
    ('CSS', False),
    # Slugs with colons might not be legacy
    (':hover', False)
])
def test_document_has_legacy_namespace(slug, legacy):
    """Excluded slugs should not update the search index."""
    assert Document(slug=slug).has_legacy_namespace == legacy


def test_document_delete_removes_tag_relationsip(root_doc):
    """Deleting a tagged document also deletes the tag relationship."""
    root_doc.tags.add('grape')
    assert TaggedDocument.objects.count() == 1
    root_doc.delete()
    assert TaggedDocument.objects.count() == 0


def test_document_raises_error_when_translating_non_localizable(root_doc):
    """Adding a translation of a non-localizable document raises an error."""
    root_doc.is_localizable = False
    root_doc.save()
    de_doc = Document(parent=root_doc, slug='Rübe', locale='de')
    with pytest.raises(ValidationError):
        de_doc.save()


def test_document_raises_error_setting_non_loc_for_trans_doc(trans_doc):
    """Setting is_localizable for a translated document raises an error."""
    en_doc = trans_doc.parent
    en_doc.is_localizable = False
    with pytest.raises(ValidationError):
        en_doc.save()


def test_document_non_english_implies_non_localizable(db):
    """All non-English documents are set non-localizable."""
    es_doc = Document.objects.create(locale='es', slug='Tubérculos')
    assert not es_doc.is_localizable


def test_document_translations(trans_doc):
    """other_translations lists other translations, English first."""
    en_doc = trans_doc.parent
    ar_doc = Document.objects.create(locale='ar', slug='جذور الخضروات',
                                     parent=en_doc)
    # Translations are returned English first, then ordered, and omit self
    assert ar_doc.locale < en_doc.locale < trans_doc.locale
    assert en_doc.other_translations == [ar_doc, trans_doc]
    assert trans_doc.other_translations == [en_doc, ar_doc]
    assert ar_doc.other_translations == [en_doc, trans_doc]


def test_document_parents(root_doc):
    """Document.parents gives the document hierarchy."""
    assert root_doc.parents == []
    child_doc = Document.objects.create(parent_topic=root_doc,
                                        slug=root_doc.slug + '/Child')
    assert child_doc.parents == [root_doc]
    gchild_doc = Document.objects.create(parent_topic=child_doc,
                                         slug=child_doc.slug + '/GrandChild')
    assert gchild_doc.parents == [root_doc, child_doc]


@pytest.mark.parametrize('url',
                         (settings.SITE_URL + '/en-US/Mozilla',
                          '/en-US/Mozilla',
                          '/',
                          ))
def test_document_redirect_allows_valid_url(db, url):
    """get_redirect_url returns valid URLs."""
    title = 'Mozilla'
    html = REDIRECT_CONTENT % {'href': url, 'title': title}
    doc = Document.objects.create(locale='en-US', slug='Redirect',
                                  is_redirect=True, html=html)
    parsed = urlparse(url)
    assert doc.get_redirect_url() == parsed.path


@pytest.mark.parametrize('url',
                         ('//evilsite.com',
                          'https://example.com/foriegn_url',
                          ))
def test_document_redirect_rejects_invalid_url(db, url):
    """get_redirect_url returns None for invalid URLs."""
    html = REDIRECT_CONTENT % {'href': url, 'title': 'Invalid URL'}
    doc = Document.objects.create(locale='en-US', slug='Redirect',
                                  is_redirect=True, html=html)
    assert doc.get_redirect_url() is None


def test_document_get_full_url(root_doc):
    """get_full_url returns full URLs."""
    assert root_doc.get_full_url() == settings.SITE_URL + '/en-US/docs/Root'


def test_document_from_url(root_doc):
    """from_url returns the document for an absolute URL."""
    doc = Document.from_url(root_doc.get_absolute_url())
    assert doc == root_doc


def test_document_from_url_locale_matches_translation(trans_doc):
    """from_url matches translation with locale plus English slug."""
    en_doc = trans_doc.parent
    url = reverse('wiki.document', locale=trans_doc.locale, args=[en_doc.slug])
    doc = Document.from_url(url)
    assert doc == trans_doc


def test_document_from_url_bad_slug_returns_none(trans_doc):
    """from_url returns None for an invalid slug."""
    en_doc = trans_doc.parent
    url = reverse('wiki.document', locale=trans_doc.locale,
                  args=[en_doc.slug + '_bad_slug'])
    doc = Document.from_url(url)
    assert doc is None


def test_document_from_url_revision_url_returns_none(create_revision):
    """from_url returns None for a revision URL."""
    doc = Document.from_url(create_revision.get_absolute_url())
    assert doc is None


def test_document_from_url_full_url_returns_doc(root_doc):
    """from_url returns the document for a full URL."""
    url = root_doc.get_full_url()
    assert Document.from_url(url) == root_doc


def test_document_from_url_other_url_returns_none(root_doc):
    """from_url returns None for a different domain."""
    assert settings.SITE_URL != 'https://example.com'
    url = 'https://example.com' + root_doc.get_absolute_url()
    assert Document.from_url(url) is None


def test_document_get_redirect_document(root_doc):
    """get_redirect_document returns the destination document."""
    old_slug = root_doc.slug
    root_doc._move_tree(new_slug='Moved')
    old_doc = Document.objects.get(slug=old_slug)
    assert old_doc.get_redirect_document() == root_doc


@pytest.mark.parametrize('invalidate_cdn_cache', (True, False))
@mock.patch('kuma.wiki.models.render_done')
def test_document_render_invalidate_cdn_cache(mock_render_done, root_doc,
                                              invalidate_cdn_cache):
    """
    The "invalidate_cdn_cache" argument to render is passed through
    as one of the arguments that the "render_done" signal provides.
    """
    root_doc.render(invalidate_cdn_cache=invalidate_cdn_cache)
    mock_render_done.send.assert_called_once_with(
        sender=root_doc.__class__,
        instance=root_doc,
        invalidate_cdn_cache=invalidate_cdn_cache
    )


class UserDocumentTests(UserTestCase):
    """Document tests which need the users fixture"""

    def test_default_topic_parents_for_translation(self):
        """A translated document with no topic parent should by default use
        the translation of its translation parent's topic parent."""
        orig_pt = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                           title='test section',
                           save=True)
        orig = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test',
                        parent_topic=orig_pt, save=True)

        trans_pt = document(locale='fr', title='le test section',
                            parent=orig_pt, save=True)
        trans = document(locale='fr', title='le test',
                         parent=orig, save=True)

        assert trans.parent_topic
        assert trans_pt.pk == trans.parent_topic.pk

    def test_default_topic_with_stub_creation(self):
        orig_pt = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                           title='test section',
                           save=True)
        orig = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test',
                        parent_topic=orig_pt, save=True)

        trans = document(locale='fr', title='le test',
                         parent=orig, save=True)

        # There should be a translation topic parent
        trans_pt = trans.parent_topic
        assert trans_pt
        # The locale of the topic parent should match the new translation
        assert trans_pt.locale == trans.locale
        # But, the translation's topic parent must *not* be the translation
        # parent's topic parent
        assert trans_pt.pk != orig_pt.pk
        # Still, since the topic parent is an autocreated stub, it shares its
        # title with the original.
        assert trans_pt.title == orig_pt.title
        # Oh, and it should point to the original parent topic as its
        # translation parent
        assert trans_pt.parent == orig_pt

    def test_default_topic_with_path_gaps(self):
        # Build a path of docs in en-US
        orig_path = ('MDN', 'web', 'CSS', 'properties', 'banana', 'leaf')
        docs, doc = [], None
        for title in orig_path:
            doc = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title=title,
                           parent_topic=doc, save=True)
            revision(document=doc, title=title, save=True)
            docs.append(doc)

        # Translate, but leave gaps for stubs
        trans_0 = document(locale='fr', title='le MDN',
                           parent=docs[0], save=True)
        revision(document=trans_0, title='le MDN', tags="LeTest!", save=True)
        trans_2 = document(locale='fr', title='le CSS',
                           parent=docs[2], save=True)
        revision(document=trans_2, title='le CSS', tags="LeTest!", save=True)
        trans_5 = document(locale='fr', title='le leaf',
                           parent=docs[5], save=True)
        revision(document=trans_5, title='le ;eaf', tags="LeTest!", save=True)

        # Make sure trans_2 got the right parent
        assert trans_2.parents[0].pk == trans_0.pk

        # Ensure the translated parents and stubs appear properly in the path
        parents_5 = trans_5.parents
        assert parents_5[0].pk == trans_0.pk
        assert parents_5[1].locale == trans_5.locale
        assert parents_5[1].title == docs[1].title
        assert parents_5[1].current_revision.pk != docs[1].current_revision.pk
        assert parents_5[2].pk == trans_2.pk
        assert parents_5[3].locale == trans_5.locale
        assert parents_5[3].title == docs[3].title
        assert parents_5[3].current_revision.pk != docs[3].current_revision.pk
        assert parents_5[4].locale == trans_5.locale
        assert parents_5[4].title == docs[4].title
        assert parents_5[4].current_revision.pk != docs[4].current_revision.pk

        for p in parents_5:
            assert p.current_revision
            if p.pk not in (trans_0.pk, trans_2.pk, trans_5.pk):
                assert 'NeedsTranslation' in p.current_revision.tags
                assert 'TopicStub' in p.current_revision.tags
                assert p.current_revision.localization_in_progress

    def test_repair_breadcrumbs(self):
        english_top = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                               title='English top',
                               save=True)
        english_mid = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                               title='English mid',
                               parent_topic=english_top,
                               save=True)
        english_bottom = document(locale=settings.WIKI_DEFAULT_LANGUAGE,
                                  title='English bottom',
                                  parent_topic=english_mid,
                                  save=True)

        french_top = document(locale='fr',
                              title='French top',
                              parent=english_top,
                              save=True)
        french_mid = document(locale='fr',
                              parent=english_mid,
                              parent_topic=english_mid,
                              save=True)
        french_bottom = document(locale='fr',
                                 parent=english_bottom,
                                 parent_topic=english_bottom,
                                 save=True)

        french_bottom.repair_breadcrumbs()
        french_bottom_fixed = Document.objects.get(locale='fr',
                                                   title=french_bottom.title)
        assert french_mid.id == french_bottom_fixed.parent_topic.id
        assert french_top.id == french_bottom_fixed.parent_topic.parent_topic.id

    def test_code_sample_extraction(self):
        """Make sure sample extraction works from the model.
        This is a smaller version of the test from test_content.py"""
        sample_html = '<p class="foo">Hello world!</p>'
        sample_css = '.foo p { color: red; }'
        sample_js = 'window.alert("Hi there!");'
        doc_src = """
            <p>This is a page. Deal with it.</p>
            <ul id="s2" class="code-sample">
                <li><pre class="brush: html">%s</pre></li>
                <li><pre class="brush: css">%s</pre></li>
                <li><pre class="brush: js">%s</pre></li>
            </ul>
            <p>More content shows up here.</p>
        """ % (escape(sample_html), escape(sample_css), escape(sample_js))

        rev = revision(is_approved=True, save=True, content=doc_src)
        result = rev.document.extract.code_sample('s2')
        assert sample_html.strip() == result['html'].strip()
        assert sample_css.strip() == result['css'].strip()
        assert sample_js.strip() == result['js'].strip()

    def test_tree_is_watched_by(self):
        rev = revision()
        testuser2 = get_user(username='testuser2')
        EditDocumentInTreeEvent.notify(testuser2, rev.document)

        assert rev.document.tree_is_watched_by(testuser2)

    def test_parent_trees_watched_by(self):
        root_doc, child_doc, grandchild_doc = create_document_tree()
        testuser2 = get_user(username='testuser2')

        EditDocumentInTreeEvent.notify(testuser2, root_doc)
        EditDocumentInTreeEvent.notify(testuser2, child_doc)

        assert 2 == len(grandchild_doc.parent_trees_watched_by(testuser2))


@pytest.mark.tags
class TaggedDocumentTests(UserTestCase):
    """Tests for tags in Documents and Revisions"""

    def test_revision_tags(self):
        """Change tags on Document by creating Revisions"""
        rev = revision(is_approved=True, save=True, content='Sample document')

        assert 0 == Document.objects.filter(tags__name='foo').count()
        assert 0 == Document.objects.filter(tags__name='alpha').count()

        r = revision(document=rev.document, content='Update to document',
                     is_approved=True, tags="foo, bar, baz")
        r.save()

        assert 1 == Document.objects.filter(tags__name='foo').count()
        assert 0 == Document.objects.filter(tags__name='alpha').count()

        r = revision(document=rev.document, content='Another update',
                     is_approved=True, tags="alpha, beta, gamma")
        r.save()

        assert 0 == Document.objects.filter(tags__name='foo').count()
        assert 1 == Document.objects.filter(tags__name='alpha').count()

    def test_duplicate_tags_with_creation(self):
        rev = revision(
            is_approved=True, save=True, content='Sample document',
            tags="test Test")
        assert rev.document.tags.count() == 1
        tag = rev.document.tags.get()
        assert tag.name in ('test', 'Test')

    def test_duplicate_tags_with_existing(self):
        dt = DocumentTag.objects.create(name='Test')
        rev = revision(
            is_approved=True, save=True, content='Sample document',
            tags="test Test")
        assert rev.document.tags.count() == 1
        tag = rev.document.tags.get()
        assert tag == dt


class RevisionTests(UserTestCase):
    """Tests for the Revision model"""

    def test_approved_revision_updates_html(self):
        """Creating an approved revision updates document.html"""
        rev = revision(is_approved=True, save=True,
                       content='Replace document html')

        assert 'Replace document html' in rev.document.html, \
               '"Replace document html" not in %s' % rev.document.html

        # Creating another approved revision replaces it again
        r = revision(document=rev.document, content='Replace html again',
                     is_approved=True)
        r.save()

        assert 'Replace html again' in rev.document.html, \
               '"Replace html again" not in %s' % rev.document.html

    def test_unapproved_revision_not_updates_html(self):
        """Creating an unapproved revision does not update document.html"""
        rev = revision(is_approved=True, save=True, content='Here to stay')

        assert 'Here to stay' in rev.document.html, \
               '"Here to stay" not in %s' % rev.document.html

        # Creating another approved revision keeps initial content
        r = revision(document=rev.document, content='Fail to replace html',
                     is_approved=False)
        r.save()

        assert 'Here to stay' in rev.document.html, \
               '"Here to stay" not in %s' % rev.document.html

    def test_revision_unicode(self):
        """Revision containing unicode characters is saved successfully."""
        content = 'Firefox informa\xe7\xf5es \u30d8\u30eb'
        rev = revision(is_approved=True, save=True, content=content)
        assert content == rev.content

    def test_save_bad_based_on(self):
        """Saving a Revision with a bad based_on value raises an error."""
        r = revision()
        r.based_on = revision()  # Revision of some other unrelated Document
        self.assertRaises(ProgrammingError, r.save)

    def test_correct_based_on_to_none(self):
        """Assure Revision.clean() changes a bad based_on value to None when
        there is no current_revision of the English document."""
        r = revision()
        r.based_on = revision()  # Revision of some other unrelated Document
        self.assertRaises(ValidationError, r.clean)
        assert r.based_on is None

    def test_correct_based_on_to_current_revision(self):
        """Assure Revision.clean() defaults based_on value to the English
        doc's current_revision when there is one."""
        # Make English rev:
        en_rev = revision(is_approved=True)
        en_rev.save()

        # Make Deutsch translation:
        de_doc = document(parent=en_rev.document, locale='de')
        de_doc.save()
        de_rev = revision(document=de_doc)

        # Set based_on to a de rev to simulate fixing broken translation source
        de_rev.based_on = de_rev
        de_rev.clean()
        assert en_rev.document.current_revision == de_rev.based_on

    def test_previous(self):
        """Revision.previous should return this revision's document's
        most recent approved revision."""
        rev = revision(is_approved=True, created=datetime(2017, 4, 15, 9, 23),
                       save=True)
        next_rev = revision(document=rev.document, content="Updated",
                            is_approved=True,
                            created=datetime(2017, 4, 15, 9, 24), save=True)
        last_rev = revision(document=rev.document, content="Finally",
                            is_approved=True,
                            created=datetime(2017, 4, 15, 9, 25), save=True)
        trans = Document.objects.create(parent=rev.document, locale='fr',
                                        title='In French')
        trans_rev = revision(document=trans, is_approved=True,
                             based_on=last_rev,
                             created=datetime(2017, 4, 15, 9, 56), save=True)

        assert rev.previous is None
        assert next_rev.previous == rev
        assert last_rev.previous == next_rev
        assert trans_rev.previous == last_rev

    @pytest.mark.toc
    def test_show_toc(self):
        """Setting toc_depth appropriately affects the Document's
        show_toc property."""
        rev = revision(is_approved=True, save=True,
                       content='Toggle table of contents.')
        assert (rev.toc_depth != 0)
        assert rev.document.show_toc

        r = revision(document=rev.document, content=rev.content, toc_depth=0,
                     is_approved=True)
        r.save()
        assert not rev.document.show_toc

        r = revision(document=rev.document, content=r.content, toc_depth=1,
                     is_approved=True)
        r.save()
        assert rev.document.show_toc

    def test_revert(self):
        """Reverting to a specific revision."""
        rev = revision(is_approved=True, save=True, content='Test reverting')
        old_id = rev.id

        revision(document=rev.document,
                 title='Test reverting',
                 content='An edit to revert',
                 comment='This edit gets reverted',
                 is_approved=True)
        rev.save()

        reverted = rev.document.revert(rev, rev.creator)
        assert 'Revert to' in reverted.comment
        assert 'Test reverting' == reverted.content
        assert old_id != reverted.id

    def test_revert_review_tags(self):
        rev = revision(is_approved=True, save=True,
                       content='Test reverting with review tags')
        rev.review_tags.set('technical')

        r2 = revision(document=rev.document,
                      title='Test reverting with review tags',
                      content='An edit to revert',
                      comment='This edit gets reverted',
                      is_approved=True)
        r2.save()
        r2.review_tags.set('editorial')

        reverted = rev.document.revert(rev, rev.creator)
        reverted_tags = [t.name for t in reverted.review_tags.all()]
        assert 'technical' in reverted_tags
        assert 'editorial' not in reverted_tags

    def test_get_tidied_content_uses_model_field_first(self):
        content = '<h1>  Test get_tidied_content.  </h1>'
        fake_tidied = '<h1>  Fake tidied.  </h1>'
        rev = revision(is_approved=True, save=True, content=content,
                       tidied_content=fake_tidied)
        assert fake_tidied == rev.get_tidied_content()

    def test_get_tidied_content_tidies_in_process_by_default(self):
        content = '<h1>  Test get_tidied_content  </h1>'
        rev = revision(is_approved=True, save=True, content=content)
        tidied_content, errors = tidy_content(
            '<h1 id="Test_get_tidied_content">  Test get_tidied_content  </h1>'
        )
        assert tidied_content == rev.get_tidied_content()

    def test_get_tidied_content_returns_none_on_allow_none(self):
        rev = revision(is_approved=True, save=True,
                       content='Test get_tidied_content can return None.')
        assert rev.get_tidied_content(allow_none=True) is None


class GetCurrentOrLatestRevisionTests(UserTestCase):

    """Tests for current_or_latest_revision."""
    def test_single_approved(self):
        """Get approved revision."""
        rev = revision(is_approved=True, save=True)
        assert rev == rev.document.current_or_latest_revision()

    def test_multiple_approved(self):
        """When multiple approved revisions exist, return the most recent."""
        r1 = revision(is_approved=True, save=True)
        r2 = revision(is_approved=True, save=True, document=r1.document)
        assert r2 == r2.document.current_or_latest_revision()

    def test_latest(self):
        """Return latest revision when no current exists."""
        r1 = revision(is_approved=False, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, save=True, document=r1.document)
        assert r2 == r1.document.current_or_latest_revision()


@override_config(
    KUMA_DOCUMENT_RENDER_TIMEOUT=600.0,
    KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT=7.0)
class DeferredRenderingTests(UserTestCase):

    def setUp(self):
        super(DeferredRenderingTests, self).setUp()
        self.rendered_content = 'THIS IS RENDERED'
        self.raw_content = 'THIS IS NOT RENDERED CONTENT'
        self.r1 = revision(is_approved=True, save=True, content='Doc 1')
        self.d1 = self.r1.document
        config.KUMA_DOCUMENT_RENDER_TIMEOUT = 600.0
        config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = 7.0

    def tearDown(self):
        super(DeferredRenderingTests, self).tearDown()
        self.d1.delete()

    def test_rendering_fields(self):
        """Defaults for model fields related to rendering should work as
        expected"""
        assert not self.d1.rendered_html
        assert not self.d1.defer_rendering
        assert not self.d1.is_rendering_scheduled
        assert not self.d1.is_rendering_in_progress

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_get_rendered(self, mock_kumascript_get):
        """get_rendered() should return rendered content when available,
        attempt a render() when it's not"""
        mock_kumascript_get.return_value = (self.rendered_content, None)

        # First, try getting the rendered version of a document. It should
        # trigger a call to kumascript.
        assert not self.d1.rendered_html
        assert not self.d1.render_started_at
        assert not self.d1.last_rendered_at
        result_rendered, _ = self.d1.get_rendered(None, 'http://testserver/')
        assert mock_kumascript_get.called
        assert self.rendered_content == result_rendered
        assert self.rendered_content == self.d1.rendered_html

        # Next, get a fresh copy of the document and try getting a rendering.
        # It should *not* call out to kumascript, because the rendered content
        # should be in the DB.
        d1_fresh = Document.objects.get(pk=self.d1.pk)
        assert self.rendered_content == d1_fresh.rendered_html
        assert d1_fresh.render_started_at
        assert d1_fresh.last_rendered_at
        mock_kumascript_get.called = False
        result_rendered, _ = d1_fresh.get_rendered(None, 'http://testserver/')
        assert not mock_kumascript_get.called
        assert self.rendered_content == result_rendered

    @mock.patch('kuma.wiki.models.render_done')
    def test_build_json_on_render(self, mock_render_done):
        """
        A document's json field is refreshed on render(), but not on save()

        bug 875349
        """
        self.d1.save()
        assert not mock_render_done.send.called
        mock_render_done.reset()

        self.d1.render()
        assert mock_render_done.send.called

    @mock.patch('kuma.wiki.kumascript.get')
    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    def test_get_summary(self, mock_kumascript_get):
        """
        get_summary() should attempt to use rendered
        """
        mock_kumascript_get.return_value = ('<p>summary!</p>', None)
        assert not self.d1.rendered_html
        result_summary = self.d1.get_summary()
        assert not mock_kumascript_get.called
        assert not self.d1.rendered_html

        self.d1.render()
        assert self.d1.rendered_html
        assert mock_kumascript_get.called
        result_summary = self.d1.get_summary()
        assert 'summary!' == result_summary

    @mock.patch('kuma.wiki.kumascript.get')
    def test_one_render_at_a_time(self, mock_kumascript_get):
        """Only one in-progress rendering should be allowed for a Document"""
        mock_kumascript_get.return_value = (self.rendered_content, None)
        self.d1.render_started_at = datetime.now()
        self.d1.save()
        with pytest.raises(DocumentRenderingInProgress):
            self.d1.render('', 'http://testserver/')

    @mock.patch('kuma.wiki.kumascript.get')
    @override_config(KUMA_DOCUMENT_RENDER_TIMEOUT=5.0)
    def test_render_timeout(self, mock_kumascript_get):
        """
        A rendering that has taken too long is no longer considered in progress
        """
        mock_kumascript_get.return_value = (self.rendered_content, None)
        self.d1.render_started_at = (datetime.now() -
                                     timedelta(seconds=5.0 + 1))
        self.d1.save()
        # No DocumentRenderingInProgress raised
        self.d1.render('', 'http://testserver/')

    @mock.patch('kuma.wiki.kumascript.get')
    def test_long_render_sets_deferred(self, mock_kumascript_get):
        """A rendering that takes more than a desired response time marks the
        document as in need of deferred rendering in the future."""
        config.KUMASCRIPT_TIMEOUT = 1.0
        rendered_content = self.rendered_content

        def my_kumascript_get(self, base_url, cache_control, timeout):
            time.sleep(1.0)
            return (rendered_content, None)

        mock_kumascript_get.side_effect = my_kumascript_get

        config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = 2.0
        self.d1.render('', 'http://testserver/')
        assert not self.d1.defer_rendering

        config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = 0.5
        self.d1.render('', 'http://testserver/')
        assert self.d1.defer_rendering
        config.KUMASCRIPT_TIMEOUT = 0.0

    @mock.patch('kuma.wiki.kumascript.get')
    @mock.patch.object(tasks.render_document, 'delay')
    def test_schedule_rendering(self, mock_render_document_delay,
                                mock_kumascript_get):
        mock_kumascript_get.return_value = (self.rendered_content, None)
        # Scheduling for a non-deferred render should happen on the spot.
        self.d1.defer_rendering = False
        self.d1.save()
        assert not self.d1.render_scheduled_at
        assert not self.d1.last_rendered_at
        self.d1.schedule_rendering(None, 'http://testserver/')
        assert self.d1.render_scheduled_at
        assert self.d1.last_rendered_at
        assert not mock_render_document_delay.called
        assert not self.d1.is_rendering_scheduled

        # Reset the significant fields and try a deferred render.
        self.d1.last_rendered_at = None
        self.d1.render_started_at = None
        self.d1.render_scheduled_at = None
        self.d1.defer_rendering = True
        self.d1.save()

        # Scheduling for a deferred render should result in a queued task.
        self.d1.schedule_rendering(None, 'http://testserver/')
        assert self.d1.render_scheduled_at
        assert not self.d1.last_rendered_at
        assert mock_render_document_delay.called

        # And, since our mock delay() doesn't actually queue a task, this
        # document should appear to be scheduled for a pending render not yet
        # in progress.
        assert self.d1.is_rendering_scheduled
        assert not self.d1.is_rendering_in_progress

    @mock.patch('kuma.wiki.kumascript.get')
    @mock.patch.object(tasks.render_document, 'delay')
    def test_immediate_rendering(self, mock_render_document_delay,
                                 mock_kumascript_get):
        '''Rendering is immediate when defer_rendering is False'''
        mock_kumascript_get.return_value = (self.rendered_content, None)
        mock_render_document_delay.side_effect = Exception('Should not be called')
        self.d1.rendered_html = ''
        self.d1.defer_rendering = False
        self.d1.save()
        result_rendered, _ = self.d1.get_rendered(None, 'http://testserver/')
        assert not mock_render_document_delay.called

    @mock.patch('kuma.wiki.kumascript.get')
    @mock.patch.object(tasks.render_document, 'delay')
    def test_deferred_rendering(self, mock_render_document_delay,
                                mock_kumascript_get):
        '''Rendering is deferred when defer_rendering is True.'''
        mock_kumascript_get.side_effect = Exception('Should not be called')
        self.d1.rendered_html = ''
        self.d1.defer_rendering = True
        self.d1.save()
        with pytest.raises(DocumentRenderedContentNotAvailable):
            self.d1.get_rendered(None, 'http://testserver/')
        assert mock_render_document_delay.called

    @mock.patch('kuma.wiki.kumascript.get')
    def test_errors_stored_correctly(self, mock_kumascript_get):
        errors = [
            {'level': 'error', 'message': 'This is a fake error',
             'args': ['FakeError']},
        ]
        mock_kumascript_get.return_value = (self.rendered_content, errors)

        r_rendered, r_errors = self.d1.get_rendered(None, 'http://testserver/')
        assert errors, r_errors


class RenderExpiresTests(UserTestCase):
    """Tests for max-age and automatic document rebuild"""

    def test_find_stale_documents(self):
        now = datetime.now()

        # Fresh
        d1 = document(title='Aged 1')
        d1.render_expires = now + timedelta(seconds=100)
        d1.save()

        # Stale, exactly now
        d2 = document(title='Aged 2')
        d2.render_expires = now
        d2.save()

        # Stale, a little while ago
        d3 = document(title='Aged 3')
        d3.render_expires = now - timedelta(seconds=100)
        d3.save()

        stale_docs = Document.objects.get_by_stale_rendering()
        assert (sorted([d2.pk, d3.pk]) ==
                sorted([x.pk for x in stale_docs]))

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_update_expires_with_max_age(self, mock_kumascript_get):
        mock_kumascript_get.return_value = ('MOCK CONTENT', None)

        max_age = 1000
        now = datetime.now()

        d1 = document(title='Aged 1')
        d1.render_max_age = max_age
        d1.save()
        d1.render()

        # HACK: Exact time comparisons suck, because execution time.
        later = now + timedelta(seconds=max_age)
        assert d1.render_expires > later - timedelta(seconds=1)
        assert d1.render_expires < later + timedelta(seconds=1)

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    def test_update_expires_without_max_age(self, mock_kumascript_get):
        mock_kumascript_get.return_value = ('MOCK CONTENT', None)

        now = datetime.now()
        d1 = document(title='Aged 1')
        d1.render_expires = now - timedelta(seconds=100)
        d1.save()
        d1.render()

        assert not d1.render_expires

    @override_config(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('kuma.wiki.kumascript.get')
    @mock.patch.object(tasks.render_document, 'delay')
    def test_render_stale(self, mock_render_document_delay,
                          mock_kumascript_get):
        mock_kumascript_get.return_value = ('MOCK CONTENT', None)

        now = datetime.now()
        earlier = now - timedelta(seconds=1000)

        d1 = document(title='Aged 3')
        d1.last_rendered_at = earlier
        d1.render_expires = now - timedelta(seconds=100)
        d1.save()

        tasks.render_stale_documents()

        d1_fresh = Document.objects.get(pk=d1.pk)
        assert not mock_render_document_delay.called
        assert d1_fresh.last_rendered_at > earlier


class PageMoveTests(UserTestCase):
    """Tests for page-moving and associated functionality."""

    @pytest.mark.move
    def test_children_simple(self):
        """A basic tree with two direct children and no sub-trees on
        either."""
        d1 = document(title='Parent', save=True)
        d2 = document(title='Child', save=True)
        d2.parent_topic = d1
        d2.save()
        d3 = document(title='Another child', save=True)
        d3.parent_topic = d1
        d3.save()

        assert [d2, d3] == d1.get_descendants()

    def test_get_descendants_limited(self):
        """Tests limiting of descendant levels"""
        def _make_doc(title, parent=None):
            doc = document(title=title, save=True)
            if parent:
                doc.parent_topic = parent
                doc.save()
            return doc

        parent = _make_doc('Parent')
        child1 = _make_doc('Child 1', parent)
        child2 = _make_doc('Child 2', parent)
        grandchild = _make_doc('GrandChild 1', child1)
        _make_doc('Great GrandChild 1', grandchild)

        # Test descendant counts
        assert 4 == len(parent.get_descendants())  # All
        assert 2 == len(parent.get_descendants(1))
        assert 3 == len(parent.get_descendants(2))
        assert 0 == len(parent.get_descendants(0))
        assert 0 == len(child2.get_descendants(10))
        assert 1 == len(grandchild.get_descendants(4))

    def test_children_complex(self):
        """A slightly more complex tree, with multiple children, some
        of which do/don't have their own children."""
        top = document(title='Parent', save=True)

        c1 = document(title='Child 1', save=True)
        c1.parent_topic = top
        c1.save()

        gc1 = document(title='Child of child 1', save=True)
        gc1.parent_topic = c1
        gc1.save()

        c2 = document(title='Child 2', save=True)
        c2.parent_topic = top
        c2.save()

        gc2 = document(title='Child of child 2', save=True)
        gc2.parent_topic = c2
        gc2.save()

        gc3 = document(title='Another child of child 2', save=True)
        gc3.parent_topic = c2
        gc3.save()

        ggc1 = document(title='Child of the second child of child 2',
                        save=True)

        ggc1.parent_topic = gc3
        ggc1.save()

        assert [c1, gc1, c2, gc2, gc3, ggc1] == top.get_descendants()

    @pytest.mark.move
    def test_circular_dependency(self):
        """Make sure we can detect potential circular dependencies in
        parent/child relationships."""
        # Test detection at one level removed.
        parent = document(title='Parent of circular-dependency document',
                          save=True)
        child = document(title='Document with circular dependency')
        child.parent_topic = parent
        child.save()

        assert child.is_child_of(parent)

        # And at two levels removed.
        grandparent = document(title='Grandparent of '
                                     'circular-dependency document')
        parent.parent_topic = grandparent
        child.save()

        assert child.is_child_of(grandparent)

    @pytest.mark.move
    def test_move_tree(self):
        """Moving a tree of documents does the correct thing"""

        # Simple multi-level tree:
        #
        #  - top
        #    - child1
        #    - child2
        #      - grandchild
        top = revision(title='Top-level parent for tree moves',
                       slug='first-level/parent',
                       is_approved=True,
                       save=True)
        old_top_id = top.id
        top_doc = top.document

        child1 = revision(title='First child of tree-move parent',
                          slug='first-level/second-level/child1',
                          is_approved=True,
                          save=True)
        old_child1_id = child1.id
        child1_doc = child1.document
        child1_doc.parent_topic = top_doc
        child1_doc.save()

        child2 = revision(title='Second child of tree-move parent',
                          slug='first-level/second-level/child2',
                          is_approved=True,
                          save=True)
        old_child2_id = child2.id
        child2_doc = child2.document
        child2_doc.parent_topic = top_doc
        child2.save()

        grandchild = revision(title='Child of second child of tree-move parent',
                              slug='first-level/second-level/third-level/grandchild',
                              is_approved=True,
                              save=True)
        old_grandchild_id = grandchild.id
        grandchild_doc = grandchild.document
        grandchild_doc.parent_topic = child2_doc
        grandchild_doc.save()

        revision(title='New Top-level bucket for tree moves',
                 slug='new-prefix',
                 is_approved=True,
                 save=True)
        revision(title='New first-level parent for tree moves',
                 slug='new-prefix/first-level',
                 is_approved=True,
                 save=True)
        # Now we do a simple move: inserting a prefix that needs to be
        # inherited by the whole tree.
        top_doc._move_tree('new-prefix/first-level/parent')

        # And for each document verify three things:
        #
        # 1. The new slug is correct.
        # 2. A new revision was created when the page moved.
        # 3. A redirect was created.
        moved_top = Document.objects.get(pk=top_doc.id)
        assert ('new-prefix/first-level/parent' ==
                moved_top.current_revision.slug)
        assert old_top_id != moved_top.current_revision.id
        assert (moved_top.current_revision.slug in
                Document.objects.get(slug='first-level/parent').get_redirect_url())

        moved_child1 = Document.objects.get(pk=child1_doc.id)
        assert ('new-prefix/first-level/parent/child1' ==
                moved_child1.current_revision.slug)
        assert old_child1_id != moved_child1.current_revision.id
        assert moved_child1.current_revision.slug in Document.objects.get(
            slug='first-level/second-level/child1').get_redirect_url()

        moved_child2 = Document.objects.get(pk=child2_doc.id)
        assert ('new-prefix/first-level/parent/child2' ==
                moved_child2.current_revision.slug)
        assert old_child2_id != moved_child2.current_revision.id
        assert moved_child2.current_revision.slug in Document.objects.get(
            slug='first-level/second-level/child2').get_redirect_url()

        moved_grandchild = Document.objects.get(pk=grandchild_doc.id)
        assert('new-prefix/first-level/parent/child2/grandchild' ==
               moved_grandchild.current_revision.slug)
        assert old_grandchild_id != moved_grandchild.current_revision.id
        assert moved_grandchild.current_revision.slug in Document.objects.get(
            slug='first-level/second-level/third-level/grandchild').get_redirect_url()

    @pytest.mark.move
    def test_conflicts(self):
        top = revision(title='Test page-move conflict detection',
                       slug='test-move-conflict-detection',
                       is_approved=True,
                       save=True)
        top_doc = top.document
        child = revision(title='Child of conflict detection test',
                         slug='move-tests/conflict-child',
                         is_approved=True,
                         save=True)
        child_doc = child.document
        child_doc.parent_topic = top_doc
        child_doc.save()

        # We should find the conflict if it's at the slug the document
        # will move to.
        top_conflict = revision(title='Conflicting document for move conflict detection',
                                slug='moved/test-move-conflict-detection',
                                is_approved=True,
                                save=True)

        assert([top_conflict.document] ==
               top_doc._tree_conflicts('moved/test-move-conflict-detection'))

        # Or if it will involve a child document.
        child_conflict = revision(title='Conflicting child for move conflict detection',
                                  slug='moved/test-move-conflict-detection/conflict-child',
                                  is_approved=True,
                                  save=True)

        assert ([top_conflict.document, child_conflict.document] ==
                top_doc._tree_conflicts('moved/test-move-conflict-detection'))

        # But a redirect should not trigger a conflict.
        revision(title='Conflicting document for move conflict detection',
                 slug='moved/test-move-conflict-detection',
                 content='REDIRECT <a class="redirect" href="/foo">Foo</a>',
                 document=top_conflict.document,
                 is_approved=True,
                 save=True)

        assert ([child_conflict.document] ==
                top_doc._tree_conflicts('moved/test-move-conflict-detection'))

    @pytest.mark.move
    def test_additional_conflicts(self):
        top = revision(title='WebRTC',
                       slug='WebRTC',
                       content='WebRTC',
                       is_approved=True,
                       save=True)
        top_doc = top.document
        child1 = revision(title='WebRTC Introduction',
                          slug='WebRTC/WebRTC_Introduction',
                          content='WebRTC Introduction',
                          is_approved=True,
                          save=True)
        child1_doc = child1.document
        child1_doc.parent_topic = top_doc
        child1_doc.save()
        child2 = revision(title='Taking webcam photos',
                          slug='WebRTC/Taking_webcam_photos',
                          is_approved=True,
                          save=True)
        child2_doc = child2.document
        child2_doc.parent_topic = top_doc
        child2_doc.save()
        assert not top_doc._tree_conflicts('NativeRTC')

    @pytest.mark.move
    def test_preserve_tags(self):
        tags = "'moving', 'tests'"
        rev = revision(title='Test page-move tag preservation',
                       slug='page-move-tags',
                       tags=tags,
                       is_approved=True,
                       save=True)
        rev.review_tags.set('technical')
        rev = Revision.objects.get(pk=rev.id)

        revision(title='New Top-level parent for tree moves',
                 slug='new-top',
                 is_approved=True,
                 save=True)

        doc = rev.document
        doc._move_tree('new-top/page-move-tags')

        moved_doc = Document.objects.get(pk=doc.id)
        new_rev = moved_doc.current_revision
        assert tags == new_rev.tags
        assert (['technical'] ==
                [str(tag) for tag in new_rev.review_tags.all()])

    @pytest.mark.move
    def test_move_tree_breadcrumbs(self):
        """Moving a tree of documents under an existing doc updates breadcrumbs"""

        grandpa = revision(title='Top-level parent for breadcrumb move',
                           slug='grandpa', is_approved=True, save=True)
        grandpa_doc = grandpa.document

        dad = revision(title='Mid-level parent for breadcrumb move',
                       slug='grandpa/dad', is_approved=True, save=True)
        dad_doc = dad.document
        dad_doc.parent_topic = grandpa_doc
        dad_doc.save()

        son = revision(title='Bottom-level child for breadcrumb move',
                       slug='grandpa/dad/son', is_approved=True, save=True)
        son_doc = son.document
        son_doc.parent_topic = dad_doc
        son_doc.save()

        grandma = revision(title='Top-level parent for breadcrumb move',
                           slug='grandma', is_approved=True, save=True)
        grandma_doc = grandma.document

        mom = revision(title='Mid-level parent for breadcrumb move',
                       slug='grandma/mom', is_approved=True, save=True)
        mom_doc = mom.document
        mom_doc.parent_topic = grandma_doc
        mom_doc.save()

        daughter = revision(title='Bottom-level child for breadcrumb move',
                            slug='grandma/mom/daughter',
                            is_approved=True,
                            save=True)
        daughter_doc = daughter.document
        daughter_doc.parent_topic = mom_doc
        daughter_doc.save()

        # move grandma under grandpa
        grandma_doc._move_tree('grandpa/grandma')

        # assert the parent_topics are correctly rooted at grandpa
        # note we have to refetch these to see any DB changes.
        grandma_moved = Document.objects.get(locale=grandma_doc.locale,
                                             slug='grandpa/grandma')
        assert grandma_moved.parent_topic == grandpa_doc
        mom_moved = Document.objects.get(locale=mom_doc.locale,
                                         slug='grandpa/grandma/mom')
        assert mom_moved.parent_topic == grandma_moved

    @pytest.mark.move
    def test_move_tree_no_new_parent(self):
        """Moving a tree to a slug that doesn't exist throws error."""

        rev = revision(title='doc to move',
                       slug='doc1', is_approved=True, save=True)
        doc = rev.document

        with pytest.raises(Exception):
            doc._move_tree('slug-that-doesnt-exist/doc1')

    @pytest.mark.move
    def test_move_top_level_docs(self):
        """Moving a top document to a new slug location"""
        page_to_move_title = 'Page Move Root'
        page_to_move_slug = 'Page_Move_Root'
        page_child_slug = 'Page_Move_Root/Page_Move_Child'
        page_moved_slug = 'Page_Move_Root_Moved'
        page_child_moved_slug = 'Page_Move_Root_Moved/Page_Move_Child'

        page_to_move_doc = document(title=page_to_move_title,
                                    slug=page_to_move_slug,
                                    save=True)
        rev = revision(document=page_to_move_doc,
                       title=page_to_move_title,
                       slug=page_to_move_slug,
                       save=True)
        page_to_move_doc.current_revision = rev
        page_to_move_doc.save()

        page_child = revision(title='child', slug=page_child_slug,
                              is_approved=True, save=True)
        page_child_doc = page_child.document
        page_child_doc.parent_topic = page_to_move_doc
        page_child_doc.save()

        # move page to new slug
        new_title = page_to_move_title + ' Moved'

        page_to_move_doc._move_tree(page_moved_slug, user=None,
                                    title=new_title)

        page_to_move_doc = Document.objects.get(slug=page_to_move_slug)
        page_moved_doc = Document.objects.get(slug=page_moved_slug)
        page_child_doc = Document.objects.get(slug=page_child_slug)
        page_child_moved_doc = Document.objects.get(slug=page_child_moved_slug)

        assert 'REDIRECT' in page_to_move_doc.html
        assert page_moved_slug in page_to_move_doc.html
        assert new_title in page_to_move_doc.html
        assert page_moved_doc
        assert 'REDIRECT' in page_child_doc.html
        assert page_moved_slug in page_child_doc.html
        assert page_child_moved_doc
        # TODO: Fix this assertion?
        # assert 'admin' == page_moved_doc.current_revision.creator.username)

    @pytest.mark.move
    def test_mid_move(self):
        root_title = 'Root'
        root_slug = 'Root'
        child_title = 'Child'
        child_slug = 'Root/Child'
        moved_child_slug = 'DiffChild'
        grandchild_title = 'Grandchild'
        grandchild_slug = 'Root/Child/Grandchild'
        moved_grandchild_slug = 'DiffChild/Grandchild'

        root_doc = document(title=root_title,
                            slug=root_slug,
                            save=True)
        rev = revision(document=root_doc,
                       title=root_title,
                       slug=root_slug,
                       save=True)
        root_doc.current_revision = rev
        root_doc.save()

        child = revision(title=child_title, slug=child_slug,
                         is_approved=True, save=True)
        child_doc = child.document
        child_doc.parent_topic = root_doc
        child_doc.save()

        grandchild = revision(title=grandchild_title,
                              slug=grandchild_slug,
                              is_approved=True, save=True)
        grandchild_doc = grandchild.document
        grandchild_doc.parent_topic = child_doc
        grandchild_doc.save()

        child_doc._move_tree(moved_child_slug)

        redirected_child = Document.objects.get(slug=child_slug)
        Document.objects.get(slug=moved_child_slug)
        assert 'REDIRECT' in redirected_child.html
        assert moved_child_slug in redirected_child.html

        redirected_grandchild = Document.objects.get(slug=grandchild_doc.slug)
        Document.objects.get(slug=moved_grandchild_slug)
        assert 'REDIRECT' in redirected_grandchild.html
        assert moved_grandchild_slug in redirected_grandchild.html

    @pytest.mark.move
    def test_move_special(self):
        root_slug = 'User:foo'
        child_slug = '%s/child' % root_slug

        new_root_slug = 'User:foobar'

        special_root = document(title='User:foo',
                                slug=root_slug,
                                save=True)
        revision(document=special_root,
                 title=special_root.title,
                 slug=root_slug,
                 save=True)

        special_child = document(title='User:foo child',
                                 slug=child_slug,
                                 save=True)
        revision(document=special_child,
                 title=special_child.title,
                 slug=child_slug,
                 save=True)

        special_child.parent_topic = special_root
        special_child.save()

        original_root_id = special_root.id
        original_child_id = special_child.id

        # First move, to new slug.
        special_root._move_tree(new_root_slug)

        # Appropriate redirects were left behind.
        root_redirect = Document.objects.get(locale=special_root.locale,
                                             slug=root_slug)
        assert root_redirect.is_redirect
        root_redirect_id = root_redirect.id
        child_redirect = Document.objects.get(locale=special_child.locale,
                                              slug=child_slug)
        assert child_redirect.is_redirect
        child_redirect_id = child_redirect.id

        # Moved documents still have the same IDs.
        moved_root = Document.objects.get(locale=special_root.locale,
                                          slug=new_root_slug)
        assert original_root_id == moved_root.id
        moved_child = Document.objects.get(locale=special_child.locale,
                                           slug='%s/child' % new_root_slug)
        assert original_child_id == moved_child.id

        # Second move, back to original slug.
        moved_root._move_tree(root_slug)

        # Once again we left redirects behind.
        root_second_redirect = Document.objects.get(locale=special_root.locale,
                                                    slug=new_root_slug)
        assert root_second_redirect.is_redirect
        child_second_redirect = Document.objects.get(locale=special_child.locale,
                                                     slug='%s/child' % new_root_slug)
        assert child_second_redirect.is_redirect

        # The documents at the original URLs aren't redirects anymore.
        rerooted_root = Document.objects.get(locale=special_root.locale,
                                             slug=root_slug)
        assert not rerooted_root.is_redirect
        rerooted_child = Document.objects.get(locale=special_child.locale,
                                              slug=child_slug)
        assert not rerooted_child.is_redirect

        # The redirects created in the first move no longer exist in the DB.
        self.assertRaises(Document.DoesNotExist,
                          Document.objects.get,
                          id=root_redirect_id)
        self.assertRaises(Document.DoesNotExist,
                          Document.objects.get,
                          id=child_redirect_id)

    def test_fail_message(self):
        """
        When page move fails in moving one of the children, it
        generates an informative exception message explaining which
        child document failed.

        """
        top = revision(title='Test page-move error messaging',
                       slug='test-move-error-messaging',
                       is_approved=True,
                       save=True)
        top_doc = top.document

        child = revision(title='Child to test page-move error messaging',
                         slug='test-move-error-messaging/child',
                         is_approved=True,
                         save=True)
        child_doc = child.document
        child_doc.parent_topic = top_doc
        child_doc.save()

        grandchild = revision(title='Grandchild to test page-move error handling',
                              slug='test-move-error-messaging/child/grandchild',
                              is_approved=True,
                              save=True)
        grandchild_doc = grandchild.document
        grandchild_doc.parent_topic = child_doc
        grandchild_doc.save()

        revision(title='Conflict page for page-move error handling',
                 slug='test-move-error-messaging/moved/grandchild',
                 is_approved=True,
                 save=True)

        mentioned_url = (
            f'https://developer.mozilla.org/{grandchild_doc.locale}'
            f'/docs/{grandchild_doc.slug}')
        with self.assertRaisesRegex(PageMoveError, mentioned_url):
            child_doc._move_tree('test-move-error-messaging/moved')


class RevisionIPTests(UserTestCase):
    def test_delete_older_than_default_30_days(self):
        old_date = date.today() - timedelta(days=31)
        r = revision(created=old_date, save=True)
        RevisionIP.objects.create(revision=r, ip='127.0.0.1').save()
        assert 1 == RevisionIP.objects.all().count()
        RevisionIP.objects.delete_old()
        assert 0 == RevisionIP.objects.all().count()

    def test_delete_older_than_days_argument(self):
        rev_date = date.today() - timedelta(days=5)
        r = revision(created=rev_date, save=True)
        RevisionIP.objects.create(revision=r, ip='127.0.0.1').save()
        assert 1 == RevisionIP.objects.all().count()
        RevisionIP.objects.delete_old(days=4)
        assert 0 == RevisionIP.objects.all().count()

    def test_delete_older_than_only_deletes_older_than(self):
        oldest_date = date.today() - timedelta(days=31)
        r1 = revision(created=oldest_date, save=True)
        RevisionIP.objects.create(revision=r1, ip='127.0.0.1').save()

        old_date = date.today() - timedelta(days=29)
        r1 = revision(created=old_date, save=True)
        RevisionIP.objects.create(revision=r1, ip='127.0.0.1').save()

        now_date = date.today()
        r2 = revision(created=now_date, save=True)
        RevisionIP.objects.create(revision=r2, ip='127.0.0.1').save()
        assert 3 == RevisionIP.objects.all().count()
        RevisionIP.objects.delete_old()
        assert 2 == RevisionIP.objects.all().count()


class AttachmentTests(UserTestCase):

    def new_attachment(self, mindtouch_attachment_id=666):
        attachment = Attachment(
            title='test attachment',
            mindtouch_attachment_id=mindtouch_attachment_id,
        )
        attachment.save()
        attachment_revision = AttachmentRevision(
            attachment=attachment,
            file='some/path.ext',
            mime_type='application/kuma',
            creator=get_user(username='admin'),
            title='test attachment',
        )
        attachment_revision.save()
        return attachment, attachment_revision

    def test_popuplate_deki_file_url(self):
        attachment, attachment_revision = self.new_attachment()
        html = ("""%s%s/@api/deki/files/%s/=""" %
                (settings.PROTOCOL, settings.ATTACHMENT_HOST,
                 attachment.mindtouch_attachment_id))
        doc = document(html=html, save=True)
        doc.populate_attachments()

        assert doc.attached_files.all().exists()
        assert 1 == doc.attached_files.all().count()
        assert attachment == doc.attached_files.first().file

    def test_popuplate_kuma_file_url(self):
        attachment, attachment_revision = self.new_attachment()
        doc = document(html=attachment.get_file_url(), save=True)
        assert not doc.attached_files.all().exists()

        populated = doc.populate_attachments()
        assert 1 == len(populated)
        assert doc.attached_files.all().exists()
        assert 1 == doc.attached_files.all().count()
        assert attachment == doc.attached_files.first().file

    def test_popuplate_multiple_attachments(self):
        attachment, attachment_revision = self.new_attachment()
        attachment2, attachment_revision2 = self.new_attachment()
        html = ("%s %s" %
                (attachment.get_file_url(), attachment2.get_file_url()))
        doc = document(html=html, save=True)
        populated = doc.populate_attachments()
        attachments = doc.attached_files.all()
        assert 2 == len(populated)
        assert attachments.exists()
        assert 2 == attachments.count()
        assert attachment == attachments[0].file
        assert attachment2 == attachments[1].file
