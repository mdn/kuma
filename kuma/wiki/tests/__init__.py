from datetime import datetime
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils.text import slugify

from html5lib.filters._base import Filter as html5lib_Filter
from nose.tools import nottest
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
    defaults = {'category': Document.CATEGORIES[0][0],
                'title': unicode(datetime.now()),
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


# I don't like this thing. revision() is more flexible. All this adds is
# is_approved=True, but it doesn't even mention approval in its name.
# TODO: Remove.
def doc_rev(content=''):
    """Save a document and an approved revision with the given content."""
    r = revision(content=content, is_approved=True)
    r.save()
    return r.document, r

# End model makers.


def new_document_data(tags=None):
    return {
        'title': 'A Test Article',
        'locale': 'en-US',
        'slug': 'a-test-article',
        'tags': ', '.join(tags or []),
        'firefox_versions': [1, 2],
        'operating_systems': [1, 3],
        'category': Document.CATEGORIES[0][0],
        'keywords': 'key1, key2',
        'summary': 'lipsum',
        'content': 'lorem ipsum dolor sit amet',
        'toc_depth': 1,
    }


def normalize_html(input):
    """Normalize HTML5 input, discarding parts not significant for
    equivalence in tests"""

    class WhitespaceRemovalFilter(html5lib_Filter):
        def __iter__(self):
            for token in html5lib_Filter.__iter__(self):
                if 'SpaceCharacters' == token['type']:
                    continue
                yield token

    return (kuma.wiki.content
            .parse(unicode(input))
            .filter(WhitespaceRemovalFilter)
            .serialize())


@nottest
def create_template_test_users():
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

    users = {}
    User = get_user_model()
    for x in ('none', 'add', 'change', 'all'):
        user, created = User.objects.get_or_create(
            username='user_%s' % x,
            defaults=dict(email='user_%s@example.com',
                          is_active=True, is_staff=False, is_superuser=False))
        if created:
            user.set_password('testpass')
            user.groups = groups.get(x, [])
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


class FakeResponse:
    """Quick and dirty mocking stand-in for a response object"""
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def read(self):
        return self.text
