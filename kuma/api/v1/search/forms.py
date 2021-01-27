from django import forms
from django.conf import settings
from django.utils.datastructures import MultiValueDict


class SearchForm(forms.Form):
    q = forms.CharField(max_length=settings.ES_Q_MAXLENGTH)
    locale = forms.MultipleChoiceField(
        required=False,
        # The `settings.LANGUAGES` looks like this:
        #   [('en-US', 'English (US)'), ...]
        # But all locales are stored in lowercase in Elasticsearch, so
        # force everything to lowercase.
        choices=[(code.lower(), name) for code, name in settings.LANGUAGES],
    )

    SORT_CHOICES = ("best", "relevance", "popularity")
    sort = forms.ChoiceField(required=False, choices=[(x, x) for x in SORT_CHOICES])

    ARCHIVE_CHOICES = ("exclude", "include", "only")
    archive = forms.ChoiceField(
        required=False, choices=[(x, x) for x in ARCHIVE_CHOICES]
    )

    size = forms.IntegerField(required=True, min_value=1, max_value=100)
    page = forms.IntegerField(required=True, min_value=1, max_value=10)

    def __init__(self, data, **kwargs):
        initial = kwargs.get("initial", {})
        # This makes it possible to supply `initial={some dict}` to the form
        # and have its values become part of the default. Normally, in Django,
        # the `SomeForm(data, initial={...})` is just used to prepopulate the
        # HTML generated form widgets.
        # See https://www.peterbe.com/plog/initial-values-bound-django-form-rendered
        data = MultiValueDict({**{k: [v] for k, v in initial.items()}, **data})

        # Because the `?locale=en-US&locale=Fr` might come in from the `request.GET`
        # we can't edit it there. So instead, we mutate it here in the `data`
        if "locale" in data:
            # Always force it to lowercase, because that's what the ChoiceField
            # is configured to. And the searches should always be in lower case.
            # Remember, Django forms will allow this to be a single string
            # (e.g. `?locale=Fr`) or a multi-value (`?locale=fr&locale=En-US`).
            if isinstance(data["locale"], str):
                data["locale"] = data["locale"].lower()
            else:
                data["locale"] = [x.lower() for x in data["locale"]]

        # If, for keys we have an initial value for, it was passed an empty string,
        # then swap it for the initial value.
        # For example `?q=searching&page=` you probably meant to omit it
        # but "allowing" it to be an empty string makes it convenient for the client.
        for key, values in data.items():
            if key in initial and values == "":
                data[key] = initial[key]

        super().__init__(data, **kwargs)
