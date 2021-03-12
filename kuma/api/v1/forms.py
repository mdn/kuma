from django import forms
from django.conf import settings


class AccountSettingsForm(forms.Form):
    locale = forms.ChoiceField(
        required=False,
        # The `settings.LANGUAGES` looks like this:
        #   [('en-US', 'English (US)'), ...]
        # But the valid choices actually come from Yari which is the only
        # one that knows which ones are really valid.
        # Here in kuma we can't enforce it as string. But at least we
        # have a complete list of all possible languages
        choices=[(code, name) for code, name in settings.LANGUAGES],
    )
