from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.utils import translation

from nose.tools import eq_
from pyquery import PyQuery as pq
import jingo

from kuma.core.tests import KumaTestCase

def setup():
    jingo.load_helpers()


class MockRequestTests(KumaTestCase):
    """Base class for tests that need a mock request"""
    rf = RequestFactory()

    def setUp(self):
        super(MockRequestTests, self).setUp()
        self.user = AnonymousUser()
        self.request = self.rf.get('/')
        self.request.user = self.user
        self.request.locale = 'en-US'


class BaseTemplateTests(MockRequestTests):
    """Tests for base.html"""

    def setUp(self):
        super(BaseTemplateTests, self).setUp()
        self.template = 'base.html'

    def test_no_dir_attribute(self):
        html = jingo.render_to_string(self.request, self.template)
        doc = pq(html)
        dir_attr = doc('html').attr['dir']
        eq_('ltr', dir_attr)

    def test_rtl_dir_attribute(self):
        translation.activate('ar')
        html = jingo.render_to_string(self.request, self.template)
        doc = pq(html)
        dir_attr = doc('html').attr['dir']
        eq_('rtl', dir_attr)


class ErrorListTests(MockRequestTests):
    """Tests for errorlist.html, which renders form validation errors."""

    def test_escaping(self):
        """Make sure we escape HTML entities, lest we court XSS errors."""
        class MockForm(object):
            errors = True
            auto_id = 'id_'

            def __iter__(self):
                return iter(self.visible_fields())

            def visible_fields(self):
                return [{'errors': ['<"evil&ness-field">']}]

            def non_field_errors(self):
                return ['<"evil&ness-non-field">']

        source = ("""{% from "includes/error_list.html" import errorlist %}"""
                  """{{ errorlist(form) }}""")
        html = jingo.render_to_string(self.request,
                                      jingo.env.from_string(source),
                                      {'form': MockForm()})
        assert '<"evil&ness' not in html
        assert '&lt;&#34;evil&amp;ness-field&#34;&gt;' in html
        assert '&lt;&#34;evil&amp;ness-non-field&#34;&gt;' in html
