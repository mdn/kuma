from django.test.client import Client
from django.test import TestCase
from django.http import HttpRequest

from nose.tools import eq_, raises
from pyquery import PyQuery as pq
import jingo
import test_utils

from sumo.urlresolvers import reverse


def setup():
    jingo.load_helpers()
    Client().get('/')


def test_breadcrumb():
    """Make sure breadcrumb links start with /."""
    c = Client()
    response = c.get(reverse('search'))

    doc = pq(response.content)
    href = doc('.breadcrumbs a')[0]
    eq_('/', href.attrib['href'][0])


class TestBaseTemplate(TestCase):
    """Tests for layout/base.html"""

    def setUp(self):
        super(TestBaseTemplate, self).setUp()

        request = test_utils.RequestFactory()
        request.locale = 'en-US'
        self.request = request
        self.template = 'layout/base.html'

    @raises(KeyError)
    def test_no_dir_attribute(self):
        """Make sure dir attr isn't rendered when no dir is specified."""
        html = jingo.render_to_string(self.request, self.template)
        doc = pq(html)
        doc('html')[0].attrib['dir']

    def test_rtl_dir_attribute(self):
        """Make sure dir attr is set to 'rtl' when specified as so."""
        html = jingo.render_to_string(self.request, self.template,
                                      {'dir': 'rtl'})
        doc = pq(html)
        dir_attr = doc('html').attr['dir']
        eq_('rtl', dir_attr)
