# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django import forms

from .models import Key


class KeyForm(forms.ModelForm):
    class Meta:
        model = Key
        fields = ('description',)
