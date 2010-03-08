# TODO: use lazy gettext, as in zamboni
import gettext
from django.utils.translation import ugettext
from django import forms
from django.conf import settings
from sumo.models import Forum, Category

def SearchForm(request):

    class _SearchForm(forms.Form):
        q = forms.CharField()

        tag = forms.CharField()

        language = forms.ChoiceField(label=ugettext('Language'), choices=settings.LANGUAGES)
        categories = []
        for cat in Category.objects.all():
            categories.append((cat.categId, cat.name))
        category = forms.ChoiceField(label=ugettext('Category'), choices=categories)

    d = request.GET.copy()
    return _SearchForm(d)
