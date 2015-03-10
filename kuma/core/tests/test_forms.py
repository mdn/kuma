from django import forms

from nose.tools import eq_
from pyquery import PyQuery as pq

from kuma.core.tests import KumaTestCase

from ..form_fields import StrippedCharField


class ExampleForm(forms.Form):
    """Example form to test a bunch of Django fields."""
    char = forms.CharField(max_length=10)
    char_optional = forms.CharField(required=False,
                                    widget=forms.TextInput())
    file = forms.FileField(max_length=10)
    choice = forms.ChoiceField(choices=((1, 1), (2, 2)))
    stripped_char = StrippedCharField(max_length=10)
    bool = forms.BooleanField()
    textarea = StrippedCharField(widget=forms.Textarea())
    email = forms.EmailField()
    url = forms.URLField(required=False, verify_exists=False)
    date = forms.DateField()
    time = forms.TimeField()


class TestFields(KumaTestCase):
    """We're not breaking CharField when monkey patching in
    kuma/core/monkeypatch.py."""
    def setUp(self):
        self.f = ExampleForm()

    def _attr_eq(self, field, attr, value):
        doc = pq(str(self.f[field]))
        eq_(value, doc.attr(attr))

    def test_char_field(self):
        self._attr_eq('char', 'required', 'required')
        self._attr_eq('stripped_char', 'maxlength', '10')

    def test_char_optional_field(self):
        self._attr_eq('char_optional', 'required', None)

    def test_file_field(self):
        self._attr_eq('file', 'required', 'required')
        self._attr_eq('stripped_char', 'maxlength', '10')

    def test_choice_field(self):
        self._attr_eq('choice', 'required', 'required')

    def test_stripped_char_field(self):
        self._attr_eq('stripped_char', 'required', 'required')
        self._attr_eq('stripped_char', 'maxlength', '10')

    def test_bool_field(self):
        self._attr_eq('bool', 'required', 'required')

    def test_textarea_field(self):
        self._attr_eq('textarea', 'required', 'required')
        # Make sure we're still calling super to get Django's defaults
        self._attr_eq('textarea', 'rows', '10')

    def test_email_field(self):
        self._attr_eq('email', 'type', 'email')
        self._attr_eq('email', 'required', 'required')

    def test_url_field(self):
        self._attr_eq('url', 'type', 'url')
        self._attr_eq('url', 'required', None)

    def test_date_field(self):
        self._attr_eq('date', 'type', 'date')
        self._attr_eq('date', 'required', 'required')

    def test_time_field(self):
        self._attr_eq('time', 'type', 'time')
        self._attr_eq('time', 'required', 'required')
