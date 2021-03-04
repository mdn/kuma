from django import forms
from django.conf import settings


# class MultipleChoiceFieldICase(forms.MultipleChoiceField):
#     """Just like forms.MultipleChoiceField but everything's case insentive.

#     For simplicity, this field assumes that each choice is a tuple where
#     the first element is always a string.
#     """

#     def valid_value(self, value):
#         return str(value).lower() in [x[0].lower() for x in self.choices]


class AccountSettingsForm(forms.Form):
    locale = forms.ChoiceField(
        required=False,
        # The `settings.LANGUAGES` looks like this:
        #   [('en-US', 'English (US)'), ...]
        # But the valid choices actually comes from Yari who is the only
        # one that knows which ones are really valid.
        # Here in kuma we can't enforce it as string. But at least we
        # have a complete list of all possible languages
        choices=[(code, name) for code, name in settings.LANGUAGES],
    )

    # def __init__(self, data, **kwargs):
    #     initial = kwargs.get("initial", {})
    #     # This makes it possible to supply `initial={some dict}` to the form
    #     # and have its values become part of the default. Normally, in Django,
    #     # the `SomeForm(data, initial={...})` is just used to prepopulate the
    #     # HTML generated form widgets.
    #     # See https://www.peterbe.com/plog/initial-values-bound-django-form-rendered
    #     data = MultiValueDict({**{k: [v] for k, v in initial.items()}, **data})

    #     # If, for keys we have an initial value for, it was passed an empty string,
    #     # then swap it for the initial value.
    #     # For example `?q=searching&page=` you probably meant to omit it
    #     # but "allowing" it to be an empty string makes it convenient for the client.
    #     for key, values in data.items():
    #         if key in initial and values == "":
    #             data[key] = initial[key]

    #     super().__init__(data, **kwargs)
