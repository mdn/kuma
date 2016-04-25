from datetime import datetime
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils.text import slugify

from html5lib.filters._base import Filter as html5lib_Filter
from waffle.models import Flag

from kuma.core.tests import get_user, KumaTestCase
from kuma.wiki.models import Document, Revision
import kuma.wiki.content


class WikiTestCase(KumaTestCase):
    """Base TestCase for the wiki app test cases."""

    def setUp(self):
        super(WikiTestCase, self).setUp()
        self.kumaediting_flag, created = Flag.objects.get_or_create(
            name='kumaediting', everyone=True)


# Model makers. These make it clearer and more concise to create objects in
# test cases. They allow the significant attribute values to stand out rather
# than being hidden amongst the values needed merely to get the model to
# validate.

def document(save=False, **kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    defaults = {'title': unicode(datetime.now()),
                'is_redirect': 0}
    defaults.update(kwargs)
    if 'slug' not in kwargs:
        defaults['slug'] = slugify(unicode(defaults['title']))
    d = Document(**defaults)
    if save:
        d.save()
    return d


def revision(save=False, **kwargs):
    """Return an empty revision with enough stuff filled out that it can be
    saved.

    Revision's is_approved=False unless you specify otherwise.

    Requires a users fixture if no creator is provided.

    """
    doc = None
    if 'document' not in kwargs:
        doc = document(save=True)
    else:
        doc = kwargs['document']

    defaults = {
        'summary': 'Some summary',
        'content': 'Some content',
        'comment': 'Some comment',
        'creator': kwargs.get('creator', get_user()),
        'document': doc,
        'tags': '"some", "tags"',
        'toc_depth': 1,
    }

    defaults.update(kwargs)

    rev = Revision(**defaults)
    if save:
        rev.save()
    return rev


def translated_revision(locale='de', **kwargs):
    """Return a revision that is the translation of a default-language one."""
    parent_rev = revision(is_approved=True)
    parent_rev.save()
    translation = document(parent=parent_rev.document,
                           locale=locale)
    translation.save()
    new_kwargs = {'document': translation, 'based_on': parent_rev}
    new_kwargs.update(kwargs)
    return revision(**new_kwargs)


def make_translation():
    # Create translation parent...
    d1 = document(title="Doc1", locale='en-US', save=True)
    revision(document=d1, save=True)

    # Then, translate it to de
    d2 = document(title="TransDoc1", locale='de', parent=d1, save=True)
    revision(document=d2, save=True)

    return d1, d2


def wait_add_rev(document):
    # Let the clock tick, then update the translation parent.
    time.sleep(1.0)
    revision(document=document, save=True)
    return document


# End model makers.


def new_document_data(tags=None):
    return {
        'title': 'A Test Article',
        'locale': 'en-US',
        'slug': 'a-test-article',
        'tags': ', '.join(tags or []),
        'firefox_versions': [1, 2],
        'operating_systems': [1, 3],
        'keywords': 'key1, key2',
        'summary': 'lipsum',
        'content': 'lorem ipsum dolor sit amet',
        'toc_depth': 1,
    }


class WhitespaceRemovalFilter(html5lib_Filter):
    def __iter__(self):
        for token in html5lib_Filter.__iter__(self):
            if 'SpaceCharacters' == token['type']:
                continue
            yield token


def normalize_html(input):
    """
    Normalize HTML5 input, discarding parts not significant for
    equivalence in tests
    """
    return (kuma.wiki.content
            .parse(unicode(input))
            .filter(WhitespaceRemovalFilter)
            .serialize(alphabetical_attributes=True))


def create_document_editor_group():
    """Get or create a group that can edit documents."""
    group, group_created = Group.objects.get_or_create(name='editor')
    if group_created:
        actions = ('add', 'change', 'delete', 'view', 'restore')
        perms = [Permission.objects.get(codename='%s_document' % action)
                 for action in actions]
        group.permissions = perms
        group.save()
    return group


def create_document_editor_user():
    """Get or create a user empowered with document editing."""
    User = get_user_model()
    user, user_created = User.objects.get_or_create(
        username='conantheeditor',
        defaults=dict(email='user_%s@example.com',
                      is_active=True, is_staff=False, is_superuser=False))
    if user_created:
        user.set_password('testpass')
        user.groups = [create_document_editor_group()]
        user.save()

    return user


def create_template_test_users():
    """Create users for template editing tests."""
    perms = dict(
        (x, [Permission.objects.get(codename='%s_template_document' % x)])
        for x in ('add', 'change',)
    )
    perms['all'] = perms['add'] + perms['change']

    groups = {}
    for x in ('add', 'change', 'all'):
        group, created = Group.objects.get_or_create(
            name='templaters_%s' % x)
        if created:
            group.permissions = perms[x]
            group.save()
        groups[x] = [group]
    editor_group = create_document_editor_group()

    users = {}
    User = get_user_model()
    for x in ('none', 'add', 'change', 'all'):
        user, created = User.objects.get_or_create(
            username='user_%s' % x,
            defaults=dict(email='user_%s@example.com',
                          is_active=True, is_staff=False, is_superuser=False))
        if created:
            user.set_password('testpass')
            user.groups = groups.get(x, []) + [editor_group]
            user.save()
        users[x] = user

    superuser, created = User.objects.get_or_create(
        username='superuser_1', defaults=dict(
            email='superuser_1@example.com',
            is_active=True, is_staff=True, is_superuser=True))
    if created:
        superuser.set_password('testpass')
        superuser.save()

    return (perms, groups, users, superuser)


def create_topical_parents_docs():
    d1 = document(title='HTML7')
    d1.save()

    d2 = document(title='Smellovision')
    d2.parent_topic = d1
    d2.save()
    return d1, d2


def create_document_tree():
    root_doc = document(title="Root", slug="Root", save=True)
    revision(document=root_doc, title="Root", slug="Root", save=True)
    child_doc = document(title="Child", slug="Child", save=True)
    child_doc.parent_topic = root_doc
    child_doc.save()
    revision(document=child_doc, title="Child", slug="Child", save=True)
    grandchild_doc = document(title="Grandchild", slug="Grandchild",
                              save=True)
    grandchild_doc.parent_topic = child_doc
    grandchild_doc.save()
    revision(document=grandchild_doc, title="Grandchild",
             slug="Grandchild", save=True)

    return root_doc, child_doc, grandchild_doc
