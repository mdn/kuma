from django import forms
from django.conf import settings
from django.utils.datastructures import MultiValueDict


class SearchForm(forms.Form):
    q = forms.CharField(max_length=200)
    locale = forms.MultipleChoiceField(
        required=False,
        # The `settings.LANGUAGES` looks like this:
        #   [('en-US', 'English (US)'), ...]
        # But all locales are stored in lowercase in Elasticsearch, so
        # force everything to lowercase.
        choices=[(code.lower(), name) for code, name in settings.LANGUAGES],
    )
    sort = forms.ChoiceField(
        required=False, choices=["best", "relevance", "popularity"]
    )
    include_archive = forms.BooleanField(required=False)
    size = forms.IntegerField(required=False, min_value=1, max_value=100)
    page = forms.IntegerField(required=False, min_value=1, max_value=10)

    def __init__(self, data, **kwargs):
        initial = kwargs.get("initial", {})
        # This makes it possible to supply `initial={some dict}` to the form
        # and have its values become part of the default. Normally, in Django,
        # the `SomeForm(data, initial={...})` is just used to prepopulate the
        # HTML generated form widgets.
        # See https://www.peterbe.com/plog/initial-values-bound-django-form-rendered
        data = MultiValueDict({**{k: [v] for k, v in initial.items()}, **data})
        super().__init__(data, **kwargs)

    # def clean_size(self):
    #     value = self.cleaned_data["size"]
    #     if value < 1:
    #         raise forms.ValidationError("too small")
    #     return value

    # def clean_page(self):
    #     value = self.cleaned_data["page"]
    #     if value < 1:
    #         raise forms.ValidationError("too small")
    #     return value
