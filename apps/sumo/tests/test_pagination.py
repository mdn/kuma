from nose.tools import eq_

import test_utils

from sumo.urlresolvers import reverse
from sumo.utils import paginate


def test_paginated_url():
    """Avoid duplicating page param in pagination."""
    url = '%s?%s' % (reverse('search'), 'q=bookmarks&page=2')
    request = test_utils.RequestFactory().get(url)
    queryset = [{}, {}]
    paginated = paginate(request, queryset)
    eq_(paginated.url,
        request.build_absolute_uri(request.path) + '?q=bookmarks')

