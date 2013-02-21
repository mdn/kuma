from nose.tools import eq_, raises
from pyquery import PyQuery as pq
import jingo
from test_utils import RequestFactory

from sumo.tests import LocalizingClient, TestCase
from sumo.urlresolvers import reverse


def setup():
    jingo.load_helpers()


def test_breadcrumb():
    """Make sure breadcrumb links start with /."""
    c = LocalizingClient()
    response = c.get(reverse('search'))

    doc = pq(response.content)
    href = doc('.breadcrumbs a')[0]
    eq_('/', href.attrib['href'][0])


class MockRequestTests(TestCase):
    """Base class for tests that need a mock request"""

    def setUp(self):
        super(MockRequestTests, self).setUp()
        request = RequestFactory()
        request.locale = 'en-US'
        self.request = request


class BaseTemplateTests(MockRequestTests):
    """Tests for base.html"""

    def setUp(self):
        super(BaseTemplateTests, self).setUp()
        self.template = 'base.html'

    @raises(KeyError)
    def test_no_dir_attribute(self):
        """Make sure dir attr isn't rendered when no dir is specified."""
        html = jingo.render_to_string(self.request.get('/'), self.template)
        doc = pq(html)
        doc('html')[0].attrib['dir']

    def test_rtl_dir_attribute(self):
        """Make sure dir attr is set to 'rtl' when specified as so."""
        html = jingo.render_to_string(self.request.get('/'), self.template,
                                      {'dir': 'rtl'})
        doc = pq(html)
        dir_attr = doc('html').attr['dir']
        eq_('rtl', dir_attr)

    def test_multi_feeds(self):
        """Ensure that multiple feeds are put into the page when set."""

        feed_urls = (('/feed_one', 'First Feed'),
                     ('/feed_two', 'Second Feed'),)

        doc = pq(jingo.render_to_string(self.request.get('/'), self.template,
                                        {'feeds': feed_urls}))
        feeds = doc('link[type="application/atom+xml"]')
        eq_(2, len(feeds))
        eq_('First Feed', feeds[0].attrib['title'])
        eq_('Second Feed', feeds[1].attrib['title'])

    def test_readonly_attr(self):
        html = jingo.render_to_string(self.request.get('/'), self.template)
        doc = pq(html)
        eq_('false', doc('body')[0].attrib['data-readonly'])


class ErrorListTests(MockRequestTests):
    """Tests for errorlist.html, which renders form validation errors."""

    def test_escaping(self):
        """Make sure we escape HTML entities, lest we court XSS errors."""
        class MockForm(object):
            errors = True
            auto_id = 'id_'

            def visible_fields(self):
                return [{'errors': ['<"evil&ness-field">']}]

            def non_field_errors(self):
                return ['<"evil&ness-non-field">']

        source = ("""{% from "layout/errorlist.html" import errorlist %}"""
                  """{{ errorlist(form) }}""")
        html = jingo.render_to_string(self.request.get('/'),
                                      jingo.env.from_string(source),
                                      {'form': MockForm()})
        assert '<"evil&ness' not in html
        assert '&lt;&#34;evil&amp;ness-field&#34;&gt;' in html
        assert '&lt;&#34;evil&amp;ness-non-field&#34;&gt;' in html
