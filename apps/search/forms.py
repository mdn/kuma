import json

from django import forms
from django.forms.util import ValidationError
from django.utils.datastructures import SortedDict

from constance import config
from tower import ugettext_lazy as _lazy


class SearchForm(forms.Form):
    q = forms.CharField(required=False)

    topic = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple,
        label=_lazy('Topic'), choices=())

    page = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['topic'].choices = self.topic_choices().items()

    def topic_choices(self):
        choices = SortedDict()
        for allowed_filter in json.loads(config.SEARCH_FILTER_TAG_OPTIONS):
            choices[allowed_filter.lower()] = allowed_filter
        return choices

    def clean_page(self):
        default = 1
        try:
            page = int(self.cleaned_data.get('page', default))
        except ValueError:
            page = default
        if page < 1:
            page = default
        return page

    def clean(self):
        if (('topic' not in self.cleaned_data or
                not self.cleaned_data['topic']) and
                self.cleaned_data['q'] == ''):
            raise ValidationError('Search requires a query string.')

        return self.cleaned_data
