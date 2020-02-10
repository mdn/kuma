import os

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template.backends.jinja2 import Jinja2
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import translation
from pyquery import PyQuery as pq

from . import KumaTestCase


class MockRequestTests(KumaTestCase):
    """Base class for tests that need a mock request"""

    rf = RequestFactory()

    def setUp(self):
        super(MockRequestTests, self).setUp()
        self.user = AnonymousUser()
        self.request = self.rf.get("/")
        self.request.user = self.user
        self.request.LANGUAGE_CODE = "en-US"


class BaseTemplateTests(MockRequestTests):
    """Tests for base.html"""

    def setUp(self):
        super(BaseTemplateTests, self).setUp()
        self.template = "base.html"

    def test_no_dir_attribute(self):
        html = render_to_string(self.template, request=self.request)
        doc = pq(html)
        dir_attr = doc("html").attr["dir"]
        assert "ltr" == dir_attr

    def test_rtl_dir_attribute(self):
        translation.activate("ar")
        html = render_to_string(self.template, request=self.request)
        doc = pq(html)
        dir_attr = doc("html").attr["dir"]
        assert "rtl" == dir_attr

    def test_lang_switcher(self):
        translation.activate("bn")
        html = render_to_string(self.template, request=self.request)
        doc = pq(html)
        # Check default locale is in the first choice field
        first_field = doc("#language.autosubmit option")[0].text_content()
        assert settings.LANGUAGE_CODE in first_field


class ErrorListTests(MockRequestTests):
    """Tests for errorlist.html, which renders form validation errors."""

    def setUp(self):
        super(ErrorListTests, self).setUp()
        params = {
            "DIRS": [os.path.join(settings.ROOT, "jinja2")],
            "APP_DIRS": True,
            "NAME": "jinja2",
            "OPTIONS": {},
        }
        self.engine = Jinja2(params)

    def test_escaping(self):
        """Make sure we escape HTML entities, lest we court XSS errors."""

        class MockForm(object):
            errors = True
            auto_id = "id_"

            def __iter__(self):
                return iter(self.visible_fields())

            def visible_fields(self):
                return [{"errors": ['<"evil&ness-field">']}]

            def non_field_errors(self):
                return ['<"evil&ness-non-field">']

        source = (
            """{% from "includes/error_list.html" import errorlist %}"""
            """{{ errorlist(form) }}"""
        )
        context = {"form": MockForm()}
        html = self.engine.from_string(source).render(context)

        assert '<"evil&ness' not in html
        assert "&lt;&#34;evil&amp;ness-field&#34;&gt;" in html
        assert "&lt;&#34;evil&amp;ness-non-field&#34;&gt;" in html
