import pyquery

from django.test.client import Client

import jingo
from nose.tools import eq_

from sumo.urlresolvers import reverse


def setup():
    jingo.load_helpers()
    Client().get('/')


def test_breadcrumb():
    """Make sure breadcrumb links start with /."""
    c = Client()
    response = c.get(reverse('search'))

    doc = pyquery.PyQuery(response.content)
    href = doc('#breadcrumbs a')[0]
    eq_('/', href.attrib['href'][0])
