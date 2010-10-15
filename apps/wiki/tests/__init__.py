from django.template.defaultfilters import slugify

from datetime import datetime

from sumo.tests import LocalizingClient, TestCase, get_user
from wiki.models import Document, Revision, CATEGORIES, SIGNIFICANCES


class TestCaseBase(TestCase):
    """Base TestCase for the wiki app test cases."""

    def setUp(self):
        super(TestCaseBase, self).setUp()
        self.client = LocalizingClient()


def document(**kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    defaults = {'category': CATEGORIES[0][0], 'title': str(datetime.now())}
    defaults.update(kwargs)
    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])
    return Document(**defaults)


def revision(**kwargs):
    """Return an empty revision with enough stuff filled out that it can be
    saved.

    Requires a users fixture if no creator is provided.

    """
    d = None
    if 'document' not in kwargs:
        d = document()
        d.save()

    defaults = {'summary': 'Some summary', 'content': 'Some content',
                'significance': SIGNIFICANCES[0][0], 'comment': 'Some comment',
                'creator': kwargs.get('creator', get_user()), 'document': d}

    defaults.update(kwargs)

    return Revision(**defaults)


# I don't like this thing. revision() is more flexible. All this adds is
# is_approved=True, but it doesn't even mention approval in its name.
# TODO: Remove.
def doc_rev(content=''):
    """Save a document and an approved revision with the given content."""
    r = revision(content=content, is_approved=True)
    r.save()
    return r.document, r


def new_document_data(tags=None):
    if tags is None:
        tags = []
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
    }
