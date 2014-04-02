
from django import forms
from sumo.form_fields import StrippedCharField

from django.conf import settings

from tower import ugettext_lazy as _lazy
from tower import ugettext as _

LANG_CHOICES = [
    ('', _lazy('All Locales'))
] + settings.LANGUAGES

class RevisionDashboardForm(forms.Form):

    locale = forms.ChoiceField(choices=LANG_CHOICES,
                    # Required for non-translations, which is
                    # enforced in Document.clean().
                    required=False,
                    label=_lazy(u'Locale:'))

    user = StrippedCharField(min_length=1, max_length=255,
                    required=False,
                    label=_lazy(u'User:'))

    topic = StrippedCharField(min_length=1, max_length=255,
                    required=False,
                    label=_lazy(u'Topic:'))

    start_date = forms.DateField(required=False, label=_lazy(u'Start Date:'),
                    input_formats=settings.DATE_INPUT_FORMATS,
                    widget = forms.TextInput(attrs={'pattern':'\d{1,2}/\d{1,2}/\d{4}'}))
    end_date = forms.DateField(required=False, label=_lazy(u'End Date:'),
                    input_formats=settings.DATE_INPUT_FORMATS,
                    widget = forms.TextInput(attrs={'pattern':'\d{1,2}/\d{1,2}/\d{4}'}))
