from django.template.defaultfilters import slugify
from django.core.cache import cache

from datetime import datetime

from sumo.tests import LocalizingClient, TestCase, get_user
from wiki.models import Document, Revision, CATEGORIES, SIGNIFICANCES


class TestCaseBase(TestCase):
    """Base TestCase for the wiki app test cases."""

    def setUp(self):
        self.client = LocalizingClient()
        cache.clear()

    def tearDown(self):
        pass


def document(**kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    auto_title = str(datetime.now())
    defaults = {'category': CATEGORIES[0][0], 'title': auto_title}
    defaults.update(kwargs)
    defaults['slug'] = slugify(defaults['title'])
    return Document(**defaults)


def revision(**kwargs):
    """Return an empty revision with enough stuff filled out that it can be
    saved.

    Requires a users fixture if no creator is provided.

    """
    u = None
    if 'creator' not in kwargs:
        u = get_user()

    d = None
    if 'document' not in kwargs:
        d = document()
        d.save()

    defaults = {'summary': 'Some summary', 'content': 'Some content',
                'significance': SIGNIFICANCES[0][0], 'comment': 'Some comment',
                'creator': u, 'document': d}

    defaults.update(kwargs)

    return Revision(**defaults)
