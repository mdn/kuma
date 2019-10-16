from datetime import datetime

import pytest

from kuma.core.urlresolvers import reverse
from kuma.wiki.constants import REDIRECT_CONTENT
from kuma.wiki.models import Document, Revision


@pytest.fixture
def redirect_to_self(wiki_user):
    """
    A top-level English document that redirects to itself.
    """
    doc = Document.objects.create(
        locale='en-US', slug='GoMe', title='Redirect to Self')
    Revision.objects.create(
        document=doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {
            'href': reverse('wiki.document', locale=doc.locale,
                            args=(doc.slug,)),
            'title': doc.title,
        },
        title='Redirect to Self',
        created=datetime(2018, 9, 16, 11, 15))
    return doc


@pytest.fixture
def redirect_to_home(wiki_user):
    """
    A top-level English document that redirects to the home page.
    """
    doc = Document.objects.create(
        locale='en-US', slug='GoHome', title='Redirect to Home Page')
    Revision.objects.create(
        document=doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {
            'href': reverse('home'),
            'title': 'MDN Web Docs',
        },
        title='Redirect to Home Page',
        created=datetime(2015, 7, 4, 11, 15))
    return doc


@pytest.fixture
def redirect_to_macros(wiki_user):
    """
    A top-level English document that redirects to the macros dashboard.
    """
    doc = Document.objects.create(
        locale='en-US', slug='GoMacros', title='Redirect to Macros Dashboard')
    Revision.objects.create(
        document=doc,
        creator=wiki_user,
        content=REDIRECT_CONTENT % {
            'href': reverse('dashboards.macros', locale='en-US'),
            'title': 'Active macros | MDN',
        },
        title='Redirect to Macros Dashboard',
        created=datetime(2017, 5, 24, 12, 15))
    return doc
