import logging
from datetime import datetime, timedelta
import json
import time
from xml.sax.saxutils import escape
from django.conf import settings

from cStringIO import StringIO

import mock
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from nose import SkipTest

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

import constance.config

from waffle.models import Flag, Switch

from sumo import ProgrammingError
from sumo.tests import TestCase

from devmo.tests import override_constance_settings

from wiki.cron import calculate_related_documents
from wiki.models import (FirefoxVersion, OperatingSystem, Document, Revision,
                         Attachment,
                         REDIRECT_CONTENT, REDIRECT_SLUG, REDIRECT_TITLE,
                         MAJOR_SIGNIFICANCE, CATEGORIES,
                         get_current_or_latest_revision,
                         DocumentRenderedContentNotAvailable,
                         DocumentRenderingInProgress,
                         TaggedDocument,)
from wiki.tests import (document, revision, doc_rev, translated_revision,
                        create_template_test_users,
                        create_topical_parents_docs)
from wiki import tasks


def _objects_eq(manager, list_):
    """Assert that the objects contained by `manager` are those in `list_`."""
    eq_(set(manager.all()), set(list_))


def redirect_rev(title, redirect_to):
    return revision(
        document=document(title=title, save=True),
        content='REDIRECT [[%s]]' % redirect_to,
        is_approved=True,
        save=True)


class AttachmentTests(TestCase):

    def test_permissions(self):
        """Ensure that the negative and positive permissions for adding
        attachments work."""
        # Get the negative and positive permissions
        ct = ContentType.objects.get(app_label='wiki', model='attachment')
        p1 = Permission.objects.get(codename='disallow_add_attachment',
                                    content_type=ct)
        p2 = Permission.objects.get(codename='add_attachment',
                                    content_type=ct)

        # Create a group with the negative permission.
        g1, created = Group.objects.get_or_create(name='cannot_attach')
        g1.permissions = [p1]
        g1.save()

        # Create a group with the positive permission.
        g2, created = Group.objects.get_or_create(name='can_attach')
        g2.permissions = [p2]
        g2.save()

        # User with no explicit permission is allowed
        u2, created = User.objects.get_or_create(username='test_user2')
        ok_(Attachment.objects.allow_add_attachment_by(u2))

        # User in group with negative permission is disallowed
        u3, created = User.objects.get_or_create(username='test_user3')
        u3.groups = [g1]
        u3.save()
        ok_(not Attachment.objects.allow_add_attachment_by(u3))

        # Superusers can do anything, despite group perms
        u1, created = User.objects.get_or_create(username='test_super',
                                                 is_superuser=True)
        u1.groups = [g1]
        u1.save()
        ok_(Attachment.objects.allow_add_attachment_by(u1))

        # User with negative permission is disallowed
        u4, created = User.objects.get_or_create(username='test_user4')
        u4.user_permissions.add(p1)
        u4.save()
        ok_(not Attachment.objects.allow_add_attachment_by(u4))

        # User with positive permission overrides group
        u5, created = User.objects.get_or_create(username='test_user5')
        u5.groups = [g1]
        u5.user_permissions.add(p2)
        u5.save()
        ok_(Attachment.objects.allow_add_attachment_by(u5))

        # Group with positive permission takes priority
        u6, created = User.objects.get_or_create(username='test_user6')
        u6.groups = [g1, g2]
        u6.save()
        ok_(Attachment.objects.allow_add_attachment_by(u6))

        # positive permission takes priority, period.
        u7, created = User.objects.get_or_create(username='test_user7')
        u7.user_permissions.add(p1)
        u7.user_permissions.add(p2)
        u7.save()
        ok_(Attachment.objects.allow_add_attachment_by(u7))


class DocumentTests(TestCase):
    """Tests for the Document model"""
    fixtures = ['test_users.json']

    @attr('bug875349')
    def test_json_data(self):
        # Set up a doc with tags
        doc, rev = doc_rev('Sample document')
        doc.save()
        expected_tags = sorted(['foo', 'bar', 'baz'])
        expected_review_tags = sorted(['tech', 'editorial'])
        doc.tags.set(*expected_tags)
        doc.current_revision.review_tags.set(*expected_review_tags)

        # Ensure the doc's json field is empty at first
        eq_(None, doc.json)

        # Get JSON data for the doc, and ensure the doc's json field is now
        # properly populated.
        data = doc.get_json_data()
        eq_(json.dumps(data), doc.json)

        # Load up another copy of the doc from the DB, and check json
        saved_doc = Document.objects.get(pk=doc.pk)
        eq_(json.dumps(data), saved_doc.json)

        # Finally, check on a few fields stored in JSON
        eq_(doc.title, data['title'])
        ok_('translations' in data)
        result_tags = sorted([str(x) for x in data['tags']])
        eq_(expected_tags, result_tags)
        result_review_tags = sorted([str(x) for x in data['review_tags']])
        eq_(expected_review_tags, result_review_tags)

    def test_document_is_template(self):
        """is_template stays in sync with the title"""
        d = document(title='test')
        d.save()

        assert not d.is_template

        d.slug = 'Template:test'
        d.save()

        assert d.is_template

        d.slug = 'Back-to-document'
        d.save()

        assert not d.is_template

    def test_error_on_delete(self):
        """Ensure error-on-delete is only thrown when waffle switch active"""
        switch = Switch.objects.create(name='wiki_error_on_delete')

        for active in (True, False):
            
            switch.active = active
            switch.save()

            d = document()
            d.save()

            try:
                d.delete()
                if active:
                    ok_(False, 'Exception on delete when active')
            except Exception, e:
                if not active:
                    ok_(False, 'No exception on delete when not active')

    def test_delete_tagged_document(self):
        """Make sure deleting a tagged doc deletes its tag relationships."""
        # TODO: Move to wherever the tests for TaggableMixin are.
        # This works because Django's delete() sees the `tags` many-to-many
        # field (actually a manager) and follows the reference.
        d = document()
        d.save()
        d.tags.add('grape')
        eq_(1, TaggedDocument.objects.count())

        d.delete()
        eq_(0, TaggedDocument.objects.count())

    def _test_m2m_inheritance(self, enum_class, attr, direct_attr):
        """Test a descriptor's handling of parent delegation."""
        parent = document()
        child = document(parent=parent, title='Some Other Title')
        e1 = enum_class(item_id=1)
        parent.save()

        # Make sure child sees stuff set on parent:
        getattr(parent, attr).add(e1)
        _objects_eq(getattr(child, attr), [e1])

        # Make sure parent sees stuff set on child:
        child.save()
        e2 = enum_class(item_id=2)
        getattr(child, attr).add(e2)
        _objects_eq(getattr(parent, attr), [e1, e2])

        # Assert the data are attached to the parent, not the child:
        _objects_eq(getattr(parent, direct_attr), [e1, e2])
        _objects_eq(getattr(child, direct_attr), [])

    def test_firefox_version_inheritance(self):
        """Assert the parent delegation of firefox_version works."""
        self._test_m2m_inheritance(FirefoxVersion, 'firefox_versions',
                                   'firefox_version_set')

    def test_operating_system_inheritance(self):
        """Assert the parent delegation of operating_system works."""
        self._test_m2m_inheritance(OperatingSystem, 'operating_systems',
                                   'operating_system_set')

    def test_category_inheritance(self):
        """A document's categories must always be those of its parent."""
        some_category = CATEGORIES[1][0]
        other_category = CATEGORIES[0][0]

        # Notice if somebody ever changes the default on the category field,
        # which would invalidate our test:
        assert some_category != document().category

        parent = document(category=some_category)
        parent.save()
        child = document(parent=parent, locale='de')
        child.save()

        # Make sure child sees stuff set on parent:
        eq_(some_category, child.category)

        # Child'd category should revert to parent's on save:
        child.category = other_category
        child.save()
        eq_(some_category, child.category)

        # Changing the parent category should change the child's:
        parent.category = other_category

        parent.save()
        eq_(other_category,
            parent.translations.get(locale=child.locale).category)

    def _test_int_sets_and_descriptors(self, enum_class, attr):
        """Test our lightweight int sets & descriptors' getting and setting."""
        d = document()
        d.save()
        _objects_eq(getattr(d, attr), [])

        i1 = enum_class(item_id=1)
        getattr(d, attr).add(i1)
        _objects_eq(getattr(d, attr), [i1])

        i2 = enum_class(item_id=2)
        getattr(d, attr).add(i2)
        _objects_eq(getattr(d, attr), [i1, i2])

    def test_firefox_versions(self):
        """Test firefox_versions attr"""
        self._test_int_sets_and_descriptors(FirefoxVersion, 'firefox_versions')

    def test_operating_systems(self):
        """Test operating_systems attr"""
        self._test_int_sets_and_descriptors(OperatingSystem,
                                            'operating_systems')

    def _test_remembering_setter_unsaved(self, field):
        """A remembering setter shouldn't kick in until the doc is saved."""
        old_field = 'old_' + field
        d = document()
        setattr(d, field, 'Foo')
        assert not hasattr(d, old_field), "Doc shouldn't have %s until it's" \
                                          "saved." % old_field

    def test_slug_setter_unsaved(self):
        self._test_remembering_setter_unsaved('slug')

    def test_title_setter_unsaved(self):
        self._test_remembering_setter_unsaved('title')

    def _test_remembering_setter(self, field):
        old_field = 'old_' + field
        d = document()
        d.save()
        old = getattr(d, field)

        # Changing the field makes old_field spring into life:
        setattr(d, field, 'Foo')
        eq_(old, getattr(d, old_field))

        # Changing it back makes old_field disappear:
        setattr(d, field, old)
        assert not hasattr(d, old_field)

        # Change it again once:
        setattr(d, field, 'Foo')

        # And twice:
        setattr(d, field, 'Bar')

        # And old_field should remain as it was, since it hasn't been saved
        # between the two changes:
        eq_(old, getattr(d, old_field))

    def test_slug_setter(self):
        """Make sure changing a slug remembers its old value."""
        self._test_remembering_setter('slug')

    def test_title_setter(self):
        """Make sure changing a title remembers its old value."""
        self._test_remembering_setter('title')

    def test_only_localizable_allowed_children(self):
        """You can't have children for a non-localizable document."""
        # Make English rev:
        en_doc = document(is_localizable=False)
        en_doc.save()

        # Make Deutsch translation:
        de_doc = document(parent=en_doc, locale='de')
        self.assertRaises(ValidationError, de_doc.save)

    def test_cannot_make_non_localizable_if_children(self):
        """You can't make a document non-localizable if it has children."""
        # Make English rev:
        en_doc = document(is_localizable=True)
        en_doc.save()

        # Make Deutsch translation:
        de_doc = document(parent=en_doc, locale='de')
        de_doc.save()
        en_doc.is_localizable = False
        self.assertRaises(ValidationError, en_doc.save)

    def test_non_english_implies_nonlocalizable(self):
        d = document(is_localizable=True, locale='de')
        d.save()
        assert not d.is_localizable

    def test_validate_category_on_save(self):
        """Make sure invalid categories can't be saved.

        Invalid categories cause errors when viewing documents.

        """
        d = document(category=9999)
        self.assertRaises(ValidationError, d.save)

    def test_new_doc_does_not_update_categories(self):
        """Make sure that creating a new document doesn't change the
        category of all the other documents."""
        d1 = document(category=10)
        d1.save()
        assert d1.pk
        d2 = document(category=00)
        assert not d2.pk
        d2._clean_category()
        d1prime = Document.objects.get(pk=d1.pk)
        eq_(10, d1prime.category)

    @attr('doc_translations')
    def test_other_translations(self):
        """
        parent doc should list all docs for which it is parent

        A child doc should list all its parent's docs, excluding itself, and
        including its parent
        """
        parent = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test', save=True)
        enfant = document(locale='fr', title='le test', parent=parent,
                         save=True)
        bambino = document(locale='es', title='el test', parent=parent,
                           save=True)

        children = Document.objects.filter(parent=parent)
        eq_(list(children), parent.other_translations)

        ok_(parent in enfant.other_translations)
        ok_(bambino in enfant.other_translations)
        eq_(False, enfant in enfant.other_translations)

    def test_topical_parents(self):
        d1, d2 = create_topical_parents_docs()
        ok_(d2.parents == [d1])

        d3 = document(title='Smell accessibility')
        d3.parent_topic = d2
        d3.save()
        ok_(d3.parents == [d1, d2])


class PermissionTests(TestCase):

    def setUp(self):
        """Set up the permissions, groups, and users needed for the tests"""
        super(PermissionTests, self).setUp()
        (self.perms, self.groups, self.users, self.superuser) = (
            create_template_test_users())

    def test_template_permissions(self):
        msg = ('should not', 'should')

        for is_add in (True, False):

            slug_trials = (
                ('test_for_%s', (
                    (True, self.superuser),
                    (True, self.users['none']),
                    (True, self.users['all']),
                    (True, self.users['add']),
                    (True, self.users['change']),
                )),
                ('Template:test_for_%s', (
                    (True,       self.superuser),
                    (False,      self.users['none']),
                    (True,       self.users['all']),
                    (is_add,     self.users['add']),
                    (not is_add, self.users['change']),
                ))
            )

            for slug_tmpl, trials in slug_trials:
                for expected, user in trials:
                    slug = slug_tmpl % user.username
                    if is_add:
                        eq_(expected,
                            Document.objects.allows_add_by(user, slug),
                            'User %s %s able to create %s' % (
                                user, msg[expected], slug))
                    else:
                        doc = document(slug=slug, title=slug)
                        eq_(expected,
                            doc.allows_revision_by(user),
                            'User %s %s able to revise %s' % (
                                user, msg[expected], slug))
                        eq_(expected,
                            doc.allows_editing_by(user),
                            'User %s %s able to edit %s' % (
                                user, msg[expected], slug))


class DocumentTestsWithFixture(TestCase):
    """Document tests which need the users fixture"""

    fixtures = ['test_users.json']

    def test_majorly_outdated(self):
        """Test the is_majorly_outdated method."""
        trans = translated_revision(is_approved=True)
        trans.save()
        trans_doc = trans.document

        # Make sure a doc returns False if it has no parent:
        assert not trans_doc.parent.is_majorly_outdated()

        assert not trans_doc.is_majorly_outdated()

        # Add a parent revision of MAJOR significance:
        r = revision(document=trans_doc.parent,
                     significance=MAJOR_SIGNIFICANCE,
                     is_approved=False)
        r.save()
        assert not trans_doc.is_majorly_outdated()

        # Approve it:
        r.is_approved = True
        r.save()

        assert trans_doc.is_majorly_outdated()

    def test_majorly_outdated_with_unapproved_parents(self):
        """Migrations might introduce translated revisions without based_on
        set. Tolerate these.

        If based_on of a translation's current_revision is None, the
        translation should be considered out of date iff any
        major-significance, approved revision to the English article exists.

        """
        # Create a parent doc with only an unapproved revision...
        parent_rev = revision()
        parent_rev.save()
        # ...and a translation with a revision based on nothing.
        trans = document(parent=parent_rev.document, locale='de')
        trans.save()
        trans_rev = revision(document=trans, is_approved=True)
        trans_rev.save()

        assert trans_rev.based_on is None, \
            ('based_on defaulted to something non-None, which this test '
             "wasn't expecting.")

        assert not trans.is_majorly_outdated(), \
            ('A translation was considered majorly out of date even though '
             'the English document has never had an approved revision of '
             'major significance.')

        major_parent_rev = revision(document=parent_rev.document,
                                    significance=MAJOR_SIGNIFICANCE,
                                    is_approved=True)
        major_parent_rev.save()

        assert trans.is_majorly_outdated(), \
            ('A translation was not considered majorly outdated when its '
             "current revision's based_on value was None.")

    def test_redirect_document_non_redirect(self):
        """Assert redirect_document on non-redirects returns None."""
        eq_(None, document().redirect_document())

    def test_redirect_document_external_redirect(self):
        """Assert redirects to external pages return None."""
        eq_(None, revision(content='REDIRECT [http://example.com]',
                           is_approved=True,
                           save=True).document.redirect_document())

    def test_redirect_document_nonexistent(self):
        """Assert redirects to non-existent pages return None."""
        eq_(None, revision(content='REDIRECT [[kersmoo]]',
                           is_approved=True,
                           save=True).document.redirect_document())

    def test_default_topic_parents_for_translation(self):
        """A translated document with no topic parent should by default use
        the translation of its translation parent's topic parent."""
        orig_pt = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test section',
                           save=True)
        orig = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test',
                        parent_topic=orig_pt, save=True)

        trans_pt = document(locale='fr', title='le test section',
                            parent=orig_pt, save=True)
        trans = document(locale='fr', title='le test',
                         parent=orig, save=True)

        ok_(trans.parent_topic)
        eq_(trans.parent_topic.pk, trans_pt.pk)

    def test_default_topic_with_stub_creation(self):
        orig_pt = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test section',
                           save=True)
        orig = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title='test',
                        parent_topic=orig_pt, save=True)

        trans = document(locale='fr', title='le test',
                         parent=orig, save=True)

        # There should be a translation topic parent
        trans_pt = trans.parent_topic
        ok_(trans_pt)
        # The locale of the topic parent should match the new translation
        eq_(trans.locale, trans_pt.locale)
        # But, the translation's topic parent must *not* be the translation
        # parent's topic parent
        ok_(trans_pt.pk != orig_pt.pk)
        # Still, since the topic parent is an autocreated stub, it shares its
        # title with the original.
        eq_(trans_pt.title, orig_pt.title)
        # Oh, and it should point to the original parent topic as its
        # translation parent
        eq_(trans_pt.parent, orig_pt)

    def test_default_topic_with_path_gaps(self):
        # Build a path of docs in en-US
        orig_path = ('MDN', 'web', 'CSS', 'properties', 'banana', 'leaf')
        docs, doc = [], None
        for title in orig_path:
            doc = document(locale=settings.WIKI_DEFAULT_LANGUAGE, title=title,
                           parent_topic=doc, save=True)
            rev = revision(document=doc, title=title, save=True)
            docs.append(doc)

        # Translate, but leave gaps for stubs
        trans_0 = document(locale='fr', title='le MDN',
                           parent=docs[0], save=True)
        trans_0_rev = revision(document=trans_0, title='le MDN',
                               tags="LeTest!",
                               save=True)
        trans_2 = document(locale='fr', title='le CSS',
                           parent=docs[2], save=True)
        trans_2_rev = revision(document=trans_2, title='le CSS',
                               tags="LeTest!",
                               save=True)
        trans_5 = document(locale='fr', title='le leaf',
                           parent=docs[5], save=True)
        trans_5_rev = revision(document=trans_5, title='le ;eaf',
                               tags="LeTest!",
                               save=True)

        # Make sure trans_2 got the right parent
        eq_(trans_2.parents[0].pk, trans_0.pk)

        # Ensure the translated parents and stubs appear properly in the path
        parents_5 = trans_5.parents
        eq_(parents_5[0].pk, trans_0.pk)
        eq_(parents_5[1].locale, trans_5.locale)
        eq_(parents_5[1].title, docs[1].title)
        ok_(parents_5[1].current_revision.pk != docs[1].current_revision.pk)
        eq_(parents_5[2].pk, trans_2.pk)
        eq_(parents_5[3].locale, trans_5.locale)
        eq_(parents_5[3].title, docs[3].title)
        ok_(parents_5[3].current_revision.pk != docs[3].current_revision.pk)
        eq_(parents_5[4].locale, trans_5.locale)
        eq_(parents_5[4].title, docs[4].title)
        ok_(parents_5[4].current_revision.pk != docs[4].current_revision.pk)

        for p in parents_5:
            ok_(p.current_revision)
            if not p.pk in (trans_0.pk, trans_2.pk, trans_5.pk):
                ok_('NeedsTranslation' in p.current_revision.tags)
                ok_('TopicStub' in p.current_revision.tags)

    def test_code_sample_extraction(self):
        """Make sure sample extraction works from the model.
        This is a smaller version of the test from test_content.py"""
        sample_html = u'<p class="foo">Hello world!</p>'
        sample_css  = u'.foo p { color: red; }'
        sample_js   = u'window.alert("Hi there!");'
        doc_src = u"""
            <p>This is a page. Deal with it.</p>
            <ul id="s2" class="code-sample">
                <li><pre class="brush: html">%s</pre></li>
                <li><pre class="brush: css">%s</pre></li>
                <li><pre class="brush: js">%s</pre></li>
            </ul>
            <p>More content shows up here.</p>
        """ % (escape(sample_html), escape(sample_css), escape(sample_js))

        d1, r1 = doc_rev(doc_src)
        result = d1.extract_code_sample('s2')
        eq_(sample_html.strip(), result['html'].strip())
        eq_(sample_css.strip(), result['css'].strip())
        eq_(sample_js.strip(), result['js'].strip())


class RedirectCreationTests(TestCase):
    """Tests for automatic creation of redirects when slug or title changes"""
    fixtures = ['test_users.json']

    def setUp(self):
        self.d, self.r = doc_rev()
        self.old_title = self.d.title
        self.old_slug = self.d.slug

    def test_change_slug(self):
        """Test proper redirect creation on slug change."""
        self.d.slug = 'new-slug'
        self.d.save()
        redirect = Document.objects.get(slug=self.old_slug)
        # "uncached" isn't necessary, but someday a worse caching layer could
        # make it so.
        attrs = dict(title=self.d.title, href=self.d.get_absolute_url())
        eq_(REDIRECT_CONTENT % attrs, redirect.current_revision.content)
        eq_(REDIRECT_TITLE % dict(old=self.d.title, number=1), redirect.title)

    def test_change_slug_and_title(self):
        """Assert only one redirect is made when both slug and title change."""
        self.d.title = 'New Title'
        self.d.slug = 'new-slug'
        self.d.save()
        attrs = dict(title=self.d.title, href=self.d.get_absolute_url())
        eq_(REDIRECT_CONTENT % attrs,
            Document.objects.get(
                slug=self.old_slug,
                title=self.old_title).current_revision.content)

    def test_no_redirect_on_unsaved_change(self):
        """No redirect should be made when an unsaved doc's title or slug is
        changed."""
        d = document(title='Gerbil')
        d.title = 'Weasel'
        d.save()
        # There should be no redirect from Gerbil -> Weasel:
        assert not Document.objects.filter(title='Gerbil').exists()

    def _test_collision_avoidance(self, attr, other_attr, template):
        """When creating redirects, dodge existing docs' titles and slugs."""
        # Create a doc called something like Whatever Redirect 1:
        document(locale=self.d.locale,
                **{other_attr: template % dict(old=getattr(self.d, other_attr),
                                               number=1)}).save()

        # Trigger creation of a redirect of a new title or slug:
        setattr(self.d, attr, 'new')
        self.d.save()

        # It should be called something like Whatever Redirect 2:
        redirect = Document.objects.get(**{attr: getattr(self,
                                                          'old_' + attr)})
        eq_(template % dict(old=getattr(self.d, other_attr),
                            number=2), getattr(redirect, other_attr))

    def test_slug_collision_avoidance(self):
        """Dodge existing slugs when making redirects due to title changes."""
        self._test_collision_avoidance('slug', 'title', REDIRECT_TITLE)

    def test_redirects_unlocalizable(self):
        """Auto-created redirects should be marked unlocalizable."""
        self.d.slug = 'new-slug'
        self.d.save()
        redirect = Document.objects.get(slug=self.old_slug)
        eq_(False, redirect.is_localizable)


class TaggedDocumentTests(TestCase):
    """Tests for tags in Documents and Revisions"""
    fixtures = ['test_users.json']

    @attr('tags')
    def test_revision_tags(self):
        """Change tags on Document by creating Revisions"""
        d, _ = doc_rev('Sample document')

        eq_(0, Document.objects.filter(tags__name='foo').count())
        eq_(0, Document.objects.filter(tags__name='alpha').count())

        r = revision(document=d, content='Update to document',
                     is_approved=True, tags="foo, bar, baz")
        r.save()

        eq_(1, Document.objects.filter(tags__name='foo').count())
        eq_(0, Document.objects.filter(tags__name='alpha').count())

        r = revision(document=d, content='Another update',
                     is_approved=True, tags="alpha, beta, gamma")
        r.save()

        eq_(0, Document.objects.filter(tags__name='foo').count())
        eq_(1, Document.objects.filter(tags__name='alpha').count())


class RevisionTests(TestCase):
    """Tests for the Revision model"""
    fixtures = ['test_users.json']

    def test_approved_revision_updates_html(self):
        """Creating an approved revision updates document.html"""
        d, _ = doc_rev('Replace document html')

        assert 'Replace document html' in d.html, \
               '"Replace document html" not in %s' % d.html

        # Creating another approved revision replaces it again
        r = revision(document=d, content='Replace html again',
                     is_approved=True)
        r.save()

        assert 'Replace html again' in d.html, \
               '"Replace html again" not in %s' % d.html

    def test_unapproved_revision_not_updates_html(self):
        """Creating an unapproved revision does not update document.html"""
        d, _ = doc_rev('Here to stay')

        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

        # Creating another approved revision keeps initial content
        r = revision(document=d, content='Fail to replace html',
                     is_approved=False)
        r.save()

        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

    def test_revision_unicode(self):
        """Revision containing unicode characters is saved successfully."""
        str = u'Firefox informa\xe7\xf5es \u30d8\u30eb'
        _, r = doc_rev(str)
        eq_(str, r.content)

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
        eq_(None, r.based_on)

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
        eq_(en_rev.document.current_revision, de_rev.based_on)

    def test_get_previous(self):
        """Revision.get_previous() should return this revision's document's
        most recent approved revision."""
        rev = revision(is_approved=True, save=True)
        eq_(None, rev.get_previous())
        # wait a second so next revision is a different datetime
        time.sleep(1)
        next_rev = revision(document=rev.document, content="Updated",
                        is_approved=True)
        next_rev.save()
        eq_(rev, next_rev.get_previous())
        time.sleep(1)
        last_rev = revision(document=rev.document, content="Finally",
                        is_approved=True)
        last_rev.save()
        eq_(next_rev, last_rev.get_previous())

    @attr('toc')
    def test_show_toc(self):
        """Setting toc_depth appropriately affects the Document's
        show_toc property."""
        d, r = doc_rev('Toggle table of contents.')
        assert (r.toc_depth != 0)
        assert d.show_toc

        r = revision(document=d, content=r.content, toc_depth=0,
                     is_approved=True)
        r.save()
        assert not d.show_toc

        r = revision(document=d, content=r.content, toc_depth=1,
                     is_approved=True)
        r.save()
        assert d.show_toc

    def test_revert(self):
        """Reverting to a specific revision."""
        d, r = doc_rev('Test reverting')
        old_id = r.id

        time.sleep(1)

        r2 = revision(document=d, title='Test reverting',
                      content='An edit to revert',
                      comment='This edit gets reverted',
                      is_approved=True)
        r.save()

        time.sleep(1)

        reverted = d.revert(r, r.creator)
        ok_('Revert to' in reverted.comment)
        ok_('Test reverting' == reverted.content)
        ok_(old_id != reverted.id)

    def test_revert_review_tags(self):
        d, r = doc_rev('Test reverting with review tags')
        r.review_tags.set('technical')
        old_id = r.id

        time.sleep(1)

        r2 = revision(document=d, title='Test reverting with review tags',
                      content='An edit to revert',
                      comment='This edit gets reverted',
                      is_approved=True)
        r2.save()
        r2.review_tags.set('editorial')

        reverted = d.revert(r, r.creator)
        reverted_tags = [t.name for t in reverted.review_tags.all()]
        ok_('technical' in reverted_tags)
        ok_('editorial' not in reverted_tags)
        
class RelatedDocumentTests(TestCase):
    fixtures = ['test_users.json', 'wiki/documents.json']

    def test_related_documents_calculated(self):
        d = Document.objects.get(pk=1)
        eq_(0, d.related_documents.count())

        calculate_related_documents()

        d = Document.objects.get(pk=1)
        eq_(2, d.related_documents.count())

    def test_related_only_locale(self):
        calculate_related_documents()
        d = Document.objects.get(pk=1)
        for rd in d.related_documents.all():
            eq_(settings.WIKI_DEFAULT_LANGUAGE, rd.locale)

    def test_only_approved_revisions(self):
        calculate_related_documents()
        d = Document.objects.get(pk=1)
        for rd in d.related_documents.all():
            assert rd.current_revision

    def test_only_approved_have_related(self):
        calculate_related_documents()
        d = Document.objects.get(pk=3)
        eq_(0, d.related_documents.count())


class GetCurrentOrLatestRevisionTests(TestCase):
    fixtures = ['test_users.json']

    """Tests for get_current_or_latest_revision."""
    def test_single_approved(self):
        """Get approved revision."""
        rev = revision(is_approved=True, save=True)
        eq_(rev, get_current_or_latest_revision(rev.document))

    def test_single_rejected(self):
        """No approved revisions available should return None."""
        rev = revision(is_approved=False)
        eq_(None, get_current_or_latest_revision(rev.document))

    def test_multiple_approved(self):
        """When multiple approved revisions exist, return the most recent."""
        r1 = revision(is_approved=True, save=True)
        r2 = revision(is_approved=True, save=True, document=r1.document)
        eq_(r2, get_current_or_latest_revision(r2.document))

    def test_approved_over_most_recent(self):
        """Should return most recently approved when there is a more recent
        unreviewed revision."""
        r1 = revision(is_approved=True, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, reviewed=None, save=True,
                      document=r1.document)
        eq_(r1, get_current_or_latest_revision(r2.document))

    def test_latest(self):
        """Return latest not-rejected revision when no current exists."""
        r1 = revision(is_approved=False, reviewed=None, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, reviewed=None, save=True,
                      document=r1.document)
        eq_(r2, get_current_or_latest_revision(r1.document))

    def test_latest_rejected(self):
        """Return latest rejected revision when no current exists."""
        r1 = revision(is_approved=False, reviewed=None, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, save=True, document=r1.document)
        eq_(r2, get_current_or_latest_revision(r1.document,
                                               reviewed_only=False))

    def test_latest_unreviewed(self):
        """Return latest unreviewed revision when no current exists."""
        r1 = revision(is_approved=False, reviewed=None, save=True,
                      created=datetime.now() - timedelta(days=1))
        r2 = revision(is_approved=False, reviewed=None, save=True,
                      document=r1.document)
        eq_(r2, get_current_or_latest_revision(r1.document,
                                               reviewed_only=False))


class DumpAndLoadJsonTests(TestCase):
    fixtures = ['test_users.json', ]

    def test_roundtrip(self):
        # Create some documents and revisions here, rather than use a fixture
        d1, r1 = doc_rev('Doc 1')
        d2, r2 = doc_rev('Doc 2')
        d3, r3 = doc_rev('Doc 3')
        d4, r4 = doc_rev('Doc 4')
        d5, r5 = doc_rev('Doc 5')

        # Since this happens in dev sometimes, break a doc by deleting its
        # current revision and leaving it with none.
        d5.current_revision = None
        d5.save()
        r5.delete()

        # The same creator will be used for all the revs, so let's also get a
        # non-creator user for the upload.
        creator = r1.creator
        uploader = User.objects.exclude(pk=creator.id).all()[0]

        # Count docs (with revisions) and revisions in DB
        doc_cnt_db = (Document.objects
                      .filter(current_revision__isnull=False)
                      .count())
        rev_cnt_db = (Revision.objects.count())

        # Do the dump, capture it, parse the JSON
        fin = StringIO()
        Document.objects.dump_json(Document.objects.all(), fin)
        data_json = fin.getvalue()
        data = json.loads(data_json)

        # No objects should come with non-null primary keys
        for x in data:
            ok_(not x['pk'])

        # Count the documents in JSON vs the DB
        doc_cnt_json = len([x for x in data if x['model'] == 'wiki.document'])
        eq_(doc_cnt_db, doc_cnt_json,
            "DB and JSON document counts should match")

        # Count the revisions in JSON vs the DB
        rev_cnt_json = len([x for x in data if x['model'] == 'wiki.revision'])
        eq_(rev_cnt_db, rev_cnt_json,
            "DB and JSON revision counts should match")

        # For good measure, ensure no documents missing revisions in the dump.
        doc_no_rev = (Document.objects
                      .filter(current_revision__isnull=True))[0]
        no_rev_cnt = len([x for x in data
                          if x['model'] == 'wiki.document' and
                             x['fields']['slug'] == doc_no_rev.slug and
                             x['fields']['locale'] == doc_no_rev.locale])
        eq_(0, no_rev_cnt,
            "There should be no document exported without revision")

        # Upload the data as JSON, assert that all objects were loaded
        loaded_cnt = Document.objects.load_json(uploader, StringIO(data_json))
        eq_(len(data), loaded_cnt)

        # Ensure the current revisions of the documents have changed, and that
        # the creator matches the uploader.
        for d_orig in (d1, d2, d3, d4):
            d_curr = Document.objects.get(pk=d_orig.pk)
            eq_(2, d_curr.revisions.count())
            ok_(d_orig.current_revision.id != d_curr.current_revision.id)
            ok_(d_orig.current_revision.creator_id !=
                d_curr.current_revision.creator_id)
            eq_(uploader.id, d_curr.current_revision.creator_id)

        # Everyone out of the pool!
        Document.objects.all().delete()
        Revision.objects.all().delete()

        # Try reloading the data on an empty DB
        loaded_cnt = Document.objects.load_json(uploader, StringIO(data_json))
        eq_(len(data), loaded_cnt)

        # Count docs (with revisions) and revisions in DB. The imported objects
        # should have beeen doc/rev pairs.
        eq_(loaded_cnt / 2, Document.objects.count())
        eq_(loaded_cnt / 2, Revision.objects.count())

        # The originals should be gone, now.
        for d_orig in (d1, d2, d3, d4):

            # The original primary key should have gone away.
            try:
                d_curr = Document.objects.get(pk=d_orig.pk)
                ok_(False, "This should have been an error")
            except Document.DoesNotExist:
                pass

            # Should be able to fetch document with the original natural key
            key = d_orig.natural_key()
            d_curr = Document.objects.get_by_natural_key(*key)
            eq_(1, d_curr.revisions.count())
            eq_(uploader.id, d_curr.current_revision.creator_id)


class DeferredRenderingTests(TestCase):
    fixtures = ['test_users.json', ]

    def setUp(self):
        super(DeferredRenderingTests, self).setUp()
        self.rendered_content = 'THIS IS RENDERED'
        self.raw_content = 'THIS IS NOT RENDERED CONTENT'
        self.d1, self.r1 = doc_rev('Doc 1')
        constance.config.KUMA_DOCUMENT_RENDER_TIMEOUT = 600.0
        constance.config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = 7.0

    def tearDown(self):
        super(DeferredRenderingTests, self).tearDown()
        self.d1.delete()

    def test_rendering_fields(self):
        """Defaults for model fields related to rendering should work as
        expected"""
        ok_(not self.d1.rendered_html)
        ok_(not self.d1.defer_rendering)
        ok_(not self.d1.is_rendering_scheduled)
        ok_(not self.d1.is_rendering_in_progress)

    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('wiki.kumascript.get')
    def test_get_rendered(self, mock_kumascript_get):
        """get_rendered() should return rendered content when available,
        attempt a render() when it's not"""
        mock_kumascript_get.return_value = (self.rendered_content, None)

        # First, try getting the rendered version of a document. It should
        # trigger a call to kumascript.
        ok_(not self.d1.rendered_html)
        ok_(not self.d1.render_started_at)
        ok_(not self.d1.last_rendered_at)
        result_rendered, _ = self.d1.get_rendered(None, 'http://testserver/')
        ok_(mock_kumascript_get.called)
        eq_(self.rendered_content, result_rendered)
        eq_(self.rendered_content, self.d1.rendered_html)

        # Next, get a fresh copy of the document and try getting a rendering.
        # It should *not* call out to kumascript, because the rendered content
        # should be in the DB.
        d1_fresh = Document.objects.get(pk=self.d1.pk)
        eq_(self.rendered_content, d1_fresh.rendered_html)
        ok_(d1_fresh.render_started_at)
        ok_(d1_fresh.last_rendered_at)
        mock_kumascript_get.called = False
        result_rendered, _ = d1_fresh.get_rendered(None, 'http://testserver/')
        ok_(not mock_kumascript_get.called)
        eq_(self.rendered_content, result_rendered)

    @attr('bug875349')
    @override_constance_settings(KUMASCRIPT_TIMEOUT=1.0)
    @mock.patch('wiki.kumascript.get')
    def test_build_json_on_render(self, mock_kumascript_get):
        """A document's json field is refreshed on render(), but not on save()"""
        mock_kumascript_get.return_value = (self.rendered_content, None)

        # Initially empty json field should be filled in after render()
        eq_(None, self.d1.json)
        self.d1.render()
        ok_(self.d1.json is not None)

        time.sleep(0.1) # Small clock-tick to age the results.

        # Change the doc title, saving does not actually change the json field.
        self.d1.title = "New title"
        self.d1.save()
        ok_(self.d1.title != self.d1.get_json_data()['title'])

        # However, rendering refreshes the json field.
        self.d1.render()
        eq_(self.d1.title, self.d1.get_json_data()['title'])

    @mock.patch('wiki.kumascript.get')
    def test_get_summary(self, mock_kumascript_get):
        """get_summary() should attempt to use rendered"""
        raise SkipTest("Transient failures here, skip for now")

        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        mock_kumascript_get.return_value = ('<p>summary!</p>', None)

        ok_(not self.d1.rendered_html)
        result_summary = self.d1.get_summary()
        ok_(mock_kumascript_get.called)
        eq_("summary!", result_summary)

        constance.config.KUMASCRIPT_TIMEOUT = 0.0

    @mock.patch('wiki.kumascript.get')
    def test_one_render_at_a_time(self, mock_kumascript_get):
        """Only one in-progress rendering should be allowed for a Document"""
        mock_kumascript_get.return_value = (self.rendered_content, None)
        self.d1.render_started_at = datetime.now()
        self.d1.save()
        try:
            self.d1.render('', 'http://testserver/')
            ok_(False, "An attempt to render while another appears to be in "
                       "progress should be disallowed")
        except DocumentRenderingInProgress:
            pass

    @mock.patch('wiki.kumascript.get')
    def test_render_timeout(self, mock_kumascript_get):
        """A rendering that has taken too long is no longer considered in progress"""
        mock_kumascript_get.return_value = (self.rendered_content, None)
        timeout = 5.0
        constance.config.KUMA_DOCUMENT_RENDER_TIMEOUT = timeout
        self.d1.render_started_at = (datetime.now() -
                                     timedelta(seconds=timeout+1))
        self.d1.save()
        try:
            self.d1.render('', 'http://testserver/')
        except DocumentRenderingInProgress:
            ok_(False, "A timed-out rendering should not be considered as still "
                       "in progress")

    @mock.patch('wiki.kumascript.get')
    def test_long_render_sets_deferred(self, mock_kumascript_get):
        """A rendering that takes more than a desired response time marks the
        document as in need of deferred rendering in the future."""
        constance.config.KUMASCRIPT_TIMEOUT = 1.0
        rendered_content = self.rendered_content
        def my_kumascript_get(self, cache_control, base_url, timeout):
            time.sleep(1.0)
            return (rendered_content, None)
        mock_kumascript_get.side_effect = my_kumascript_get

        constance.config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = 2.0
        self.d1.render('', 'http://testserver/')
        ok_(not self.d1.defer_rendering)

        constance.config.KUMA_DOCUMENT_FORCE_DEFERRED_TIMEOUT = 0.5
        self.d1.render('', 'http://testserver/')
        ok_(self.d1.defer_rendering)
        constance.config.KUMASCRIPT_TIMEOUT = 0.0

    @mock.patch('wiki.kumascript.get')
    @mock.patch_object(tasks.render_document, 'delay')
    def test_schedule_rendering(self, mock_render_document_delay,
                                mock_kumascript_get):
        mock_kumascript_get.return_value = (self.rendered_content, None)
        
        # Scheduling for a non-deferred render should happen on the spot.
        self.d1.defer_rendering = False
        self.d1.save()
        ok_(not self.d1.render_scheduled_at)
        ok_(not self.d1.last_rendered_at)
        self.d1.schedule_rendering(None, 'http://testserver/')
        ok_(self.d1.render_scheduled_at)
        ok_(self.d1.last_rendered_at)
        ok_(not mock_render_document_delay.called)
        ok_(not self.d1.is_rendering_scheduled)

        # Reset the significant fields and try a deferred render.
        self.d1.last_rendered_at = None
        self.d1.render_started_at = None
        self.d1.render_scheduled_at = None
        self.d1.defer_rendering = True
        self.d1.save()

        # Scheduling for a deferred render should result in a queued task.
        self.d1.schedule_rendering(None, 'http://testserver/')
        ok_(self.d1.render_scheduled_at)
        ok_(not self.d1.last_rendered_at)
        ok_(mock_render_document_delay.called)

        # And, since our mock delay() doesn't actually queue a task, this
        # document should appear to be scheduled for a pending render not yet
        # in progress.
        ok_(self.d1.is_rendering_scheduled)
        ok_(not self.d1.is_rendering_in_progress)

    @mock.patch('wiki.kumascript.get')
    @mock.patch_object(tasks.render_document, 'delay')
    def test_deferred_vs_immediate_rendering(self, mock_render_document_delay,
                                             mock_kumascript_get):
        mock_kumascript_get.return_value = (self.rendered_content, None)

        switch = Switch.objects.create(name='wiki_force_immediate_rendering')

        # When defer_rendering == False, the rendering should be immediate.
        switch.active = False
        switch.save()
        self.d1.rendered_html = ''
        self.d1.defer_rendering = False
        self.d1.save()
        result_rendered, _ = self.d1.get_rendered(None, 'http://testserver/')
        ok_(not mock_render_document_delay.called)

        # When defer_rendering == True but the waffle switch forces immediate,
        # the rendering should be immediate.
        switch.active = True
        switch.save()
        self.d1.rendered_html = ''
        self.d1.defer_rendering = True
        self.d1.save()
        result_rendered, _ = self.d1.get_rendered(None, 'http://testserver/')
        ok_(not mock_render_document_delay.called)

        # When defer_rendering == True, the rendering should be deferred and an
        # exception raised if the content is blank.
        switch.active = False
        switch.save()
        self.d1.rendered_html = ''
        self.d1.defer_rendering = True
        self.d1.save()
        try:
            result_rendered, _ = self.d1.get_rendered(None, 'http://testserver/')
            ok_(False, "We should have gotten a "
                       "DocumentRenderedContentNotAvailable exception")
        except DocumentRenderedContentNotAvailable:
            pass
        ok_(mock_render_document_delay.called)

    @mock.patch('wiki.kumascript.get')
    def test_errors_stored_correctly(self, mock_kumascript_get):
        errors = [
            {'level': 'error', 'message': 'This is a fake error',
             'args': ['FakeError']},
        ]
        mock_kumascript_get.return_value = (self.rendered_content, errors)

        r_rendered, r_errors = self.d1.get_rendered(None, 'http://testserver/')
        ok_(errors, r_errors)

class PageMoveTests(TestCase):
    """Tests for page-moving and associated functionality."""

    fixtures = ['test_users.json']

    @attr('move')
    def test_children_simple(self):
        """A basic tree with two direct children and no sub-trees on
        either."""
        d1 = document(title='Parent')
        d2 = document(title='Child')
        d2.parent_topic = d1
        d2.save()
        d3 = document(title='Another child')
        d3.parent_topic = d1
        d3.save()

        eq_([d2, d3], d1.get_descendants())

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
        greatgrandchild = _make_doc('Great GrandChild 1', grandchild)

        # Test descendant counts
        eq_(len(parent.get_descendants()), 4)  #All
        eq_(len(parent.get_descendants(1)), 2)
        eq_(len(parent.get_descendants(2)), 3)
        eq_(len(parent.get_descendants(0)), 0)
        eq_(len(child2.get_descendants(10)), 0)
        eq_(len(grandchild.get_descendants(4)), 1)

    @attr('move')
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

        ok_([c1, gc1, c2, gc2, gc3, ggc1] == top.get_descendants())

    @attr('move')
    def test_circular_dependency(self):
        """Make sure we can detect potential circular dependencies in
        parent/child relationships."""
        # Test detection at one level removed.
        parent = document(title='Parent of circular-dependency document')
        child = document(title='Document with circular dependency')
        child.parent_topic = parent
        child.save()

        ok_(child.is_child_of(parent))

        # And at two levels removed.
        grandparent = document(title='Grandparent of circular-dependency document')
        parent.parent_topic = grandparent
        child.save()

        ok_(child.is_child_of(grandparent))

    def test_has_children(self):
        parent = document(title='Parent document for testing has_children()')
        child = document(title='Child document for testing has_children()')
        child.parent_topic = parent
        child.save()

        ok_(parent.has_children())
    
    @attr('move')
    def test_move(self):
        """Changing title/slug leaves behind a redirect document"""
        rev = revision(title='Page that will be moved',
                       slug='page-that-will-be-moved')
        rev.is_approved = True
        rev.save()

        moved = revision(document=rev.document,
                         title='Page that has been moved',
                         slug='page-that-has-been-moved')
        moved.is_approved = True
        moved.save()

        d = Document.objects.get(slug='page-that-will-be-moved')
        ok_(d.id != rev.document.id)
        ok_('page-that-has-been-moved' in d.redirect_url())

    @attr('move')
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

        # Now we do a simple move: inserting a prefix that needs to be
        # inherited by the whole tree.
        top_doc._move_tree('new-prefix/first-level/parent')

        # And for each document verify three things:
        #
        # 1. The new slug is correct.
        # 2. A new revision was created when the page moved.
        # 3. A redirect was created.
        moved_top = Document.objects.get(pk=top_doc.id)
        eq_('new-prefix/first-level/parent',
            moved_top.current_revision.slug)
        ok_(old_top_id != moved_top.current_revision.id)
        ok_(moved_top.current_revision.slug in \
            Document.objects.get(slug='first-level/parent').redirect_url())

        moved_child1 = Document.objects.get(pk=child1_doc.id)
        eq_('new-prefix/first-level/parent/child1',
            moved_child1.current_revision.slug)
        ok_(old_child1_id != moved_child1.current_revision.id)
        ok_(moved_child1.current_revision.slug in \
            Document.objects.get(slug='first-level/second-level/child1').redirect_url())

        moved_child2 = Document.objects.get(pk=child2_doc.id)
        eq_('new-prefix/first-level/parent/child2',
            moved_child2.current_revision.slug)
        ok_(old_child2_id != moved_child2.current_revision.id)
        ok_(moved_child2.current_revision.slug in \
            Document.objects.get(slug='first-level/second-level/child2').redirect_url())

        moved_grandchild = Document.objects.get(pk=grandchild_doc.id)
        eq_('new-prefix/first-level/parent/child2/grandchild',
            moved_grandchild.current_revision.slug)
        ok_(old_grandchild_id != moved_grandchild.current_revision.id)
        ok_(moved_grandchild.current_revision.slug in \
            Document.objects.get(slug='first-level/second-level/third-level/grandchild').redirect_url())

    @attr('move')
    def test_move_prepend(self):
        """Test the special-case prepend logic."""
        top = revision(title='Top-level parent for testing moves with prependings',
                       slug='parent',
                       is_approved=True,
                       save=True)
        top_doc = top.document

        child1 = revision(title='First child of tree-move-prepending parent',
                          slug='first-level/child1',
                          is_approved=True,
                          save=True)
        child1_doc = child1.document
        child1_doc.parent_topic = top_doc
        child1_doc.save()

        top_doc._move_tree('new-prefix/parent')
        moved_top = Document.objects.get(pk=top_doc.id)
        eq_('new-prefix/parent',
            moved_top.current_revision.slug)

        moved_child1 = Document.objects.get(pk=child1_doc.id)
        eq_('new-prefix/parent/child1',
            moved_child1.current_revision.slug)
            
    @attr('move')
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

        eq_([top_conflict.document],
            top_doc._tree_conflicts('moved/test-move-conflict-detection'))

        # Or if it will involve a child document.
        child_conflict = revision(title='Conflicting child for move conflict detection',
                                  slug='moved/test-move-conflict-detection/conflict-child',
                                  is_approved=True,
                                  save=True)

        eq_([top_conflict.document, child_conflict.document],
            top_doc._tree_conflicts('moved/test-move-conflict-detection'))

        # But a redirect should not trigger a conflict.
        conflict_redirect = revision(title='Conflicting document for move conflict detection',
                                     slug='moved/test-move-conflict-detection',
                                     content='REDIRECT <a class="redirect" href="/foo">Foo</a>',
                                     document=top_conflict.document,
                                     is_approved=True,
                                     save=True)

        eq_([child_conflict.document],
            top_doc._tree_conflicts('moved/test-move-conflict-detection'))

    @attr('move')
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
        child1_doc.parent_topic= top_doc
        child1_doc.save()
        child2 = revision(title='Taking webcam photos',
                          slug='WebRTC/Taking_webcam_photos',
                          is_approved=True,
                          save=True)
        child2_doc = child2.document
        child2_doc.parent_topic = top_doc
        child2_doc.save()
        eq_([],
            top_doc._tree_conflicts('NativeRTC'))

    @attr('move')
    def test_preserve_tags(self):
            tags = "'moving', 'tests'"
            rev = revision(title='Test page-move tag preservation',
                           slug='page-move-tags',
                           tags=tags,
                           is_approved=True,
                           save=True)
            rev.review_tags.set('technical')
            rev = Revision.objects.get(pk=rev.id)

            doc = rev.document
            doc._move_tree('move/page-move-tags')

            moved_doc = Document.objects.get(pk=doc.id)
            new_rev = moved_doc.current_revision
            eq_(tags, new_rev.tags)
            eq_(['technical'],
                [str(tag) for tag in new_rev.review_tags.all()])
