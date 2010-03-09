from django import forms
from django.conf import settings

from sumo.models import Forum, Category

# TODO: use lazy gettext, as in zamboni
import gettext
from django.utils.translation import ugettext

# constants are defined in __init__.py
import search

def SearchForm(request):

    class _SearchForm(forms.Form):
        q = forms.CharField()

        # kb form data
        tag = forms.CharField(label=ugettext('Tags'))

        language = forms.ChoiceField(label=ugettext('Language'), choices=settings.LANGUAGES)

        categories = []
        for cat in Category.objects.all():
            categories.append((cat.categId, cat.name))
        category = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            label=ugettext('Category'), choices=categories)

        # forum form data
        status = forms.ChoiceField(label=ugettext('Post status'), choices=search.STATUS_LIST)
        author = forms.CharField()

        created = forms.ChoiceField(label=ugettext('Created'), choices=search.CREATED_LIST)
        created_date = forms.CharField()

        lastmodif = forms.ChoiceField(label=ugettext('Last updated'), choices=search.LUP_LIST)
        sortby = forms.ChoiceField(label=ugettext('Sort results by'), choices=search.SORTBY_LIST)

        forums = []
        for f in Forum.objects.all():
            forums.append((f.forumId, f.name))
        fid = forms.MultipleChoiceField(label=ugettext('Search in forum'), choices=forums)


    d = request.GET.copy()
    return _SearchForm(d)
