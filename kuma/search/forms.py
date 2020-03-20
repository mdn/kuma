from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Index


class IndexModelForm(forms.ModelForm):
    class Meta:
        model = Index
        fields = ["created_at", "name", "promoted", "populated"]

    def clean(self):
        current_index = Index.objects.get_current()
        if current_index.successor:
            raise ValidationError(
                _(
                    "There is already a successor to "
                    "the current index %s" % current_index
                )
            )
        return self.cleaned_data
