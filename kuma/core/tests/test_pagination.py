from django.test import RequestFactory
from nose.tools import eq_
import pyquery

from ..urlresolvers import reverse
from ..utils import paginate
from ..helpers import paginator


def test_paginated_url():
    """Avoid duplicating page param in pagination."""
    url = '%s?%s' % (reverse('search'), 'q=bookmarks&page=2')
    request = RequestFactory().get(url)
    queryset = [{}, {}]
    paginated = paginate(request, queryset)
    eq_(paginated.url,
        request.build_absolute_uri(request.path) + '?q=bookmarks')


def test_invalid_page_param():
    url = '%s?%s' % (reverse('search'), 'page=a')
    request = RequestFactory().get(url)
    queryset = range(100)
    paginated = paginate(request, queryset)
    eq_(paginated.url,
        request.build_absolute_uri(request.path) + '?')


def test_paginator_filter():

    # Correct number of <li>s on page 1.
    url = reverse('search')
    request = RequestFactory().get(url)
    pager = paginate(request, range(100), per_page=9)
    html = paginator(pager)
    doc = pyquery.PyQuery(html)
    eq_(11, len(doc('li')))

    # Correct number of <li>s in the middle.
    url = '%s?%s' % (reverse('search'), 'page=10')
    request = RequestFactory().get(url)
    pager = paginate(request, range(200), per_page=10)
    html = paginator(pager)
    doc = pyquery.PyQuery(html)
    eq_(13, len(doc('li')))
