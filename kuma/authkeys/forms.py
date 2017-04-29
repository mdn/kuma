from django import forms

from .models import Key


class KeyForm(forms.ModelForm):
    class Meta(object):
        model = Key
        fields = ('description',)
