from django import forms
from django.conf import settings

from tower import ugettext_lazy as _
from sumo.form_fields import StrippedCharField


LANG_CHOICES = [('', _('All Locales'))] + settings.LANGUAGES


class RevisionDashboardForm(forms.Form):

    locale = forms.ChoiceField(choices=LANG_CHOICES,
                    # Required for non-translations, which is
                    # enforced in Document.clean().
                    required=False,
                    label=_(u'Locale:'))

    user = StrippedCharField(min_length=1, max_length=255,
                    required=False,
                    label=_(u'User:'))

    topic = StrippedCharField(min_length=1, max_length=255,
                    required=False,
                    label=_(u'Topic:'))

    start_date = forms.DateField(required=False, label=_(u'Start Date:'),
                    input_formats=['%m/%d/%Y'],
                    widget=forms.TextInput(attrs={'pattern': '\d{1,2}/\d{1,2}/\d{4}'}))

    end_date = forms.DateField(required=False, label=_(u'End Date:'),
                    input_formats=['%m/%d/%Y'],
                    widget=forms.TextInput(attrs={'pattern': '\d{1,2}/\d{1,2}/\d{4}'}))
