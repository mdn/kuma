from datetime import datetime

from django.template.defaultfilters import slugify

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter

import waffle
from waffle.models import Flag, Sample, Switch

from sumo.tests import LocalizingClient, TestCase, get_user
import wiki.content
from wiki.models import Document, Revision, CATEGORIES, SIGNIFICANCES

class TestCaseBase(TestCase):
    """Base TestCase for the wiki app test cases."""

    def setUp(self):
        super(TestCaseBase, self).setUp()
        self.client = LocalizingClient()
        
        self.kumawiki_flag = Flag.objects.create(name='kumawiki',
                                                 everyone=True)

    def tearDown(self):
        self.kumawiki_flag.delete()


# Model makers. These make it clearer and more concise to create objects in
# test cases. They allow the significant attribute values to stand out rather
# than being hidden amongst the values needed merely to get the model to
# validate.

def document(save=False, **kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    defaults = {'category': CATEGORIES[0][0], 'title': str(datetime.now())}
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
    d = None
    if 'document' not in kwargs:
        d = document()
        d.save()

    defaults = {'summary': 'Some summary', 'content': 'Some content',
                'significance': SIGNIFICANCES[0][0], 'comment': 'Some comment',
                'creator': kwargs.get('creator', get_user()), 'document': d}

    defaults.update(kwargs)

    r = Revision(**defaults)
    if save:
        r.save()
    return r


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
        'slug': 'a-test-article',
        'tags': tags or [],
        'firefox_versions': [1, 2],
        'operating_systems': [1, 3],
        'category': CATEGORIES[0][0],
        'keywords': 'key1, key2',
        'summary': 'lipsum',
        'content': 'lorem ipsum dolor sit amet',
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

    return (wiki.content
            .parse(unicode(input))
            .filter(WhitespaceRemovalFilter)
            .serialize())
