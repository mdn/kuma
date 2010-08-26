from django.contrib.auth.models import User
from django.core.cache import cache

from sumo.tests import LocalizingClient, TestCase
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
    if 'category' not in kwargs:
        kwargs['category'] = CATEGORIES[0][0]  # arbitrary
    return Document(**kwargs)


def revision(**kwargs):
    """Return an empty revision with enough stuff filled out that it can be
    saved."""
    u = None
    if 'creator' not in kwargs:
        try:
            u = User.objects.get(username='testuser')
        except User.DoesNotExist:
            u = User(username='testuser', email='me@nobody.test')
            u.save()

    d = None
    if 'document' not in kwargs:
        d = document()
        d.save()

    defaults = {'summary': 'Some summary', 'content': 'Some content',
                'significance': SIGNIFICANCES[0][0], 'comment': 'Some comment',
                'creator': u, 'document': d}

    defaults.update(kwargs)

    return Revision(**defaults)
