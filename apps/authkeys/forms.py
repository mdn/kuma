from django import forms

from .models import Key


class KeyForm(forms.ModelForm):
    class Meta:
        model = Key
        fields = ('description',)
