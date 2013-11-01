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


class RawSearchForm(forms.Form):

    locale = forms.CharField(max_length=255, required=False,
        label="Locale (filter)")

    tags = forms.CharField(max_length=255, required=False,
        label='Tags (filter)')

    kumascript_macros = forms.CharField(max_length=255, required=False,
        label='KumaScript macros')
    
    css_classnames = forms.CharField(max_length=255, required=False,
        label='CSS classes')
    
    html_attributes = forms.CharField(max_length=255, required=False,
        label='HTML attributes')

    filter_field_names = (
        'locale', 'tags'
    )
    search_field_names = (
        'kumascript_macros', 'css_classnames',
        'html_attributes'
    )
    
    def clean(self):
        at_least_one = False
        for field in self.search_field_names:
            if self.cleaned_data.get(field, None):
                at_least_one = True
        if not at_least_one:
            raise ValidationError('Search terms in at least one field is'
                                  ' required')
        return self.cleaned_data
