from __future__ import unicode_literals

from datetime import datetime

from django.contrib.auth.models import Group, Permission
from django.utils.text import slugify
from html5lib.filters.base import Filter as html5lib_Filter
from waffle.models import Flag

import kuma.wiki.content
from kuma.core.tests import get_user, KumaTestCase

from ..models import Document, Revision


HREFLANG_TEST_CASES = {
    'no-country': [['ar', 'ca', 'he'], ['ar', 'ca', 'he']],
    'single-country': [['hi-IN', 'sv-SE'], ['hi', 'sv']],
    'pt-preferred-only': [['pt-PT'], ['pt']],
    'pt-non-preferred-only': [['pt-BR'], ['pt']],
    'pt-both': [['pt-PT', 'pt-BR'], ['pt', 'pt-BR']],
    'zh-preferred-only': [['zh-CN'], ['zh']],
    'zh-non-preferred-only': [['zh-TW'], ['zh']],
    'zh-both': [['zh-CN', 'zh-TW'], ['zh', 'zh-TW']],
}


class WikiTestCase(KumaTestCase):
    """Base TestCase for the wiki app test cases."""

    def setUp(self):
        super(WikiTestCase, self).setUp()
        self.kumaediting_flag, created = Flag.objects.get_or_create(
            name='kumaediting', everyone=True)

    def tearDown(self):
        super(WikiTestCase, self).setUp()
        self.kumaediting_flag.delete()


# Model makers. These make it clearer and more concise to create objects in
# test cases. They allow the significant attribute values to stand out rather
# than being hidden amongst the values needed merely to get the model to
# validate.

def document(save=False, **kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    defaults = {'title': datetime.now(),
                'is_redirect': 0}
    defaults.update(kwargs)
    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])
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
        'creator': kwargs.get('creator') or get_user(),
        'document': doc,
        'tags': '"some", "tags"',
        'toc_depth': 1,
    }

    defaults.update(kwargs)

    rev = Revision(**defaults)
    if save:
        rev.save()
    return rev


def make_translation():
    # Create translation parent...
    d1 = document(title="Doc1", locale='en-US', save=True)
    revision(document=d1, save=True)

    # Then, translate it to de
    d2 = document(title="TransDoc1", locale='de', parent=d1, save=True)
    revision(document=d2, save=True)

    return d1, d2


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


def normalize_html(html):
    """
    Normalize HTML5 input, discarding parts not significant for
    equivalence in tests
    """
    return (kuma.wiki.content
            .parse(html)
            .filter(WhitespaceRemovalFilter)
            .serialize())


def create_document_editor_group():
    """Get or create a group that can edit documents."""
    group = Group.objects.create(name='editor')
    actions = ('add', 'change', 'delete', 'view', 'restore')
    perms = [Permission.objects.get(codename='%s_document' % action)
             for action in actions]
    group.permissions = perms
    group.save()
    return group


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
