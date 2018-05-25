# TODO: We should consider deleting this file after moving to Django 1.11,
#       since there would probably be no further need to confirm Django's
#       handling of the "required" and "type" attributes when rendering
#       a field as a widget.
from django import forms
from pyquery import PyQuery as pq
import pytest

from ..form_fields import StrippedCharField


FIELD_TESTS = {
    'char-required': ('char', 'required', True),
    'char_optional-required': ('char_optional', 'required', False),
    'file-required': ('file', 'required', True),
    'choice-required': ('choice', 'required', True),
    'stripped_char-maxlength': ('stripped_char', 'maxlength', '10'),
    'stripped_char-required': ('stripped_char', 'required', True),
    'bool-required': ('bool', 'required', True),
    'textarea-rows': ('textarea', 'rows', '10'),
    'textarea-required': ('textarea', 'required', True),
    'email-type': ('email', 'type', 'email'),
    'email-required': ('email', 'required', True),
    'url-type': ('url', 'type', 'url'),
    'url-required': ('url', 'required', False),
    'date-required': ('date', 'required', True),
    'time-required': ('time', 'required', True),
}


class ExampleForm(forms.Form):
    """Example form to test a bunch of Django fields."""
    char = forms.CharField(max_length=10)
    char_optional = forms.CharField(required=False,
                                    widget=forms.TextInput())
    file = forms.FileField(max_length=10)
    choice = forms.ChoiceField(choices=(('', ''), (1, 1), (2, 2)))
    stripped_char = StrippedCharField(max_length=10)
    bool = forms.BooleanField()
    textarea = StrippedCharField(widget=forms.Textarea())
    email = forms.EmailField()
    url = forms.URLField(required=False)
    date = forms.DateField()
    time = forms.TimeField()


@pytest.mark.parametrize('field,attr,expected_val', FIELD_TESTS.values(),
                         ids=FIELD_TESTS.keys())
def test_field(field, attr, expected_val):
    form = ExampleForm()
    rendered_field = str(form[field])
    actual_val = pq(rendered_field).attr(attr)
    if attr == 'required':
        if expected_val:
            assert actual_val in ('', 'required')
        else:
            assert actual_val is None
    else:
        assert actual_val == expected_val
